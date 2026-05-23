from fastapi import APIRouter
from typing import Dict, List, Tuple
from datetime import datetime, timezone
import json
import os

router = APIRouter()

ANALYTICS_FILE = "analytics_data.json"


def _utc_now_iso() -> str:
    """UTC ISO timestamp, naive (no offset) — comparable as a string to other UTC ISO strings."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def load_analytics() -> Dict:
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("reviews", [])
    data.setdefault("suggestions", [])
    stats = data.setdefault("stats", {})
    stats.setdefault("total", 0)
    stats.setdefault("issues_found", 0)
    stats.setdefault("suggestions_accepted", 0)
    return data


def save_analytics(data: Dict) -> None:
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(data, f)
        f.write("\n")


@router.get("/dashboard")
async def get_dashboard_data() -> Dict:
    """Get dashboard statistics"""
    data = load_analytics()
    recent_reviews = data["reviews"][-10:]

    total_suggestions = len(data["suggestions"])
    accepted = data["stats"]["suggestions_accepted"]
    acceptance_rate = (accepted / total_suggestions) if total_suggestions else 0.0

    return {
        "stats": {
            "totalReviews": data["stats"]["total"],
            "issuesFound": data["stats"]["issues_found"],
            "suggestionsPosted": total_suggestions,
            "suggestionsAccepted": accepted,
            "acceptanceRate": round(acceptance_rate, 4),
        },
        "recentReviews": recent_reviews,
    }


def record_review(repository: str, pr_number: int, issues_found: int, response_time: float = 0) -> None:
    """Record a completed review"""
    data = load_analytics()
    data["reviews"].append({
        "repository": repository,
        "prNumber": pr_number,
        "issuesFound": issues_found,
        "responseTime": response_time,
        "timestamp": datetime.now().isoformat(),
    })
    data["stats"]["total"] += 1
    data["stats"]["issues_found"] += issues_found
    save_analytics(data)


def record_suggestions(suggestions: List[Dict]) -> None:
    """Record posted suggestions so their acceptance can be tracked later.

    Each item: {repository, prNumber, file, line, startLine?, endLine?}
    """
    if not suggestions:
        return
    data = load_analytics()
    now = _utc_now_iso()
    for s in suggestions:
        data["suggestions"].append({
            "repository": s["repository"],
            "prNumber": s["prNumber"],
            "file": s["file"],
            "line": s.get("line"),
            "startLine": s.get("startLine"),
            "endLine": s.get("endLine"),
            "postedAt": now,
            "accepted": False,
            "acceptedAt": None,
        })
    save_analytics(data)


def mark_accepted_suggestions(
    repository: str,
    pr_number: int,
    accepted_events_by_file: Dict[str, List[Tuple[str, int, int]]],
) -> int:
    """Mark pending suggestions accepted when an accept-commit range overlaps theirs.

    `accepted_events_by_file` maps filename -> list of (commit_date_iso, start, end).
    An event only counts toward a suggestion when commit_date > suggestion.postedAt
    (a commit that predates the suggestion can't be its acceptance).

    Idempotent: already-accepted rows are skipped.
    """
    if not accepted_events_by_file:
        return 0
    data = load_analytics()
    newly = 0
    now = _utc_now_iso()
    for s in data["suggestions"]:
        if s["accepted"]:
            continue
        if s["repository"] != repository or s["prNumber"] != pr_number:
            continue
        events = accepted_events_by_file.get(s["file"])
        if not events:
            continue
        sug_start = s["startLine"] or s["line"]
        sug_end = s["endLine"] or s["line"]
        if sug_start is None or sug_end is None:
            continue
        posted_at = s.get("postedAt") or ""
        for ev_date, r_start, r_end in events:
            if ev_date and posted_at and ev_date <= posted_at:
                # commit predates suggestion — can't be its acceptance
                continue
            if r_start <= sug_end and r_end >= sug_start:
                s["accepted"] = True
                s["acceptedAt"] = now
                newly += 1
                break
    if newly:
        data["stats"]["suggestions_accepted"] += newly
        save_analytics(data)
    return newly
