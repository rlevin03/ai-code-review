from app.core.github_client import github_client
from app.core.ai_analyzer import analyze_code
from app.api.analytics import record_review, record_suggestions, mark_accepted_suggestions
import logging
import re
import time
from datetime import timezone
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# GitHub uses these commit-message titles when a user clicks "Commit suggestion(s)"
# in the PR UI. They're the only reliable signal that a suggestion was accepted.
ACCEPT_COMMIT_PATTERN = re.compile(r"^Apply suggestions? from code review", re.IGNORECASE)


def _extract_added_line_ranges(patch: str) -> List[Tuple[int, int]]:
    """Return contiguous added-line ranges on the new (RHS) side of a unified diff."""
    if not patch:
        return []
    ranges: List[Tuple[int, int]] = []
    current_start = current_end = None
    new_line = 0
    for line in patch.split('\n'):
        if line.startswith('@@'):
            m = re.search(r'\+(\d+)', line)
            if m:
                new_line = int(m.group(1)) - 1
            if current_start is not None:
                ranges.append((current_start, current_end))
                current_start = current_end = None
        elif line.startswith('+++') or line.startswith('---'):
            continue
        elif line.startswith('+'):
            new_line += 1
            if current_start is None:
                current_start = new_line
            current_end = new_line
        elif line.startswith('-'):
            continue
        else:
            new_line += 1
            if current_start is not None:
                ranges.append((current_start, current_end))
                current_start = current_end = None
    if current_start is not None:
        ranges.append((current_start, current_end))
    return ranges


def check_accepted_suggestions(repo, pr, repo_name: str, pr_number: int) -> int:
    """Scan PR commits for GitHub's 'Apply suggestion' commits and mark matches accepted.

    Idempotent: already-accepted suggestions are skipped, so re-scanning every
    synchronize event is safe.
    """
    accepted_events_by_file: Dict[str, List[Tuple[str, int, int]]] = {}
    for commit in pr.get_commits():
        first_line = (commit.commit.message or "").split('\n', 1)[0]
        if not ACCEPT_COMMIT_PATTERN.match(first_line):
            continue
        # Normalize commit date to a naive-UTC ISO string so it sorts against
        # the postedAt strings written by record_suggestions.
        commit_dt = commit.commit.committer.date if commit.commit.committer else None
        if commit_dt is not None:
            if commit_dt.tzinfo is not None:
                commit_dt = commit_dt.astimezone(timezone.utc).replace(tzinfo=None)
            commit_date_iso = commit_dt.isoformat()
        else:
            commit_date_iso = ""
        # PR-commits endpoint doesn't include file diffs; re-fetch the commit
        # via the repo endpoint to get its patches.
        detailed = repo.get_commit(commit.sha)
        for f in detailed.files or []:
            for r_start, r_end in _extract_added_line_ranges(f.patch or ""):
                accepted_events_by_file.setdefault(f.filename, []).append(
                    (commit_date_iso, r_start, r_end)
                )
    return mark_accepted_suggestions(repo_name, pr_number, accepted_events_by_file)

async def handle_pull_request(payload: dict):
    """Process a pull request event"""
    start_time = time.time()
    repo_name = payload['repository']['full_name']
    pr_number = payload['pull_request']['number']
    action = payload.get('action')

    gh = None
    try:
        # Get installation access token
        installation_id = payload['installation']['id']
        gh = github_client.get_installation_client(installation_id)

        # Get the repository and PR
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # A synchronize event may have been triggered by the user clicking
        # "Commit suggestion" — check before re-reviewing.
        if action == "synchronize":
            try:
                newly_accepted = check_accepted_suggestions(repo, pr, repo_name, pr_number)
                if newly_accepted:
                    logger.info(f"Marked {newly_accepted} suggestion(s) accepted on PR #{pr_number}")
            except Exception as e:
                logger.warning(f"Acceptance check failed for PR #{pr_number}: {e}")

        # Post initial comment
        pr.create_issue_comment("🤖 AI Code Review started...")
        
        # Get the files changed in the PR
        files = pr.get_files()
        
        # Analyze each file
        all_comments = []
        issues_count = 0
        
        for file in files:
            if file.filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                # Get the patch
                if not file.patch:
                    continue
                    
                # Analyze the code
                analysis = await analyze_code(
                    filename=file.filename,
                    patch=file.patch,
                    full_content=None  #TODO: Add full content
                )
                
                # Add review comments (as GitHub suggestions)
                if analysis and analysis.get('issues'):
                    for issue in analysis['issues']:
                        suggestion_text = issue.get('suggestion')
                        if not suggestion_text:
                            continue

                        issues_count += 1
                        severity = issue.get('severity', 'info').upper()
                        message = issue.get('message', 'Suggestion')
                        comment_body = (
                            f"**{severity}**: {message}\n\n"
                            f"```suggestion\n{suggestion_text}\n```"
                        )

                        start_line = issue.get('start_line')
                        end_line = issue.get('end_line')
                        target_line = issue.get('line')

                        comment_payload = {
                            'path': file.filename,
                            'body': comment_body,
                            'side': 'RIGHT'
                        }

                        # Multi-line suggestion with proper ordering
                        if start_line and end_line:
                            sl = int(start_line)
                            el = int(end_line)
                            if sl == el:
                                # Convert to single-line anchor
                                comment_payload['line'] = sl
                            else:
                                if sl > el:
                                    sl, el = el, sl
                                comment_payload['start_line'] = sl
                                comment_payload['line'] = el
                                comment_payload['start_side'] = 'RIGHT'
                        elif target_line:
                            # Single-line anchor: only 'line'
                            tl = int(target_line)
                            comment_payload['line'] = tl
                        else:
                            # No anchor line; skip
                            continue

                        all_comments.append(comment_payload)
        
        # Submit the review
        if all_comments:
            head_sha = pr.head.sha
            head_commit = repo.get_commit(head_sha)
            # GitHub limits to 30 comments per review
            for i in range(0, len(all_comments), 30):
                batch = all_comments[i:i+30]
                pr.create_review(
                    body=f"AI Code Review (Part {i//30 + 1})" if len(all_comments) > 30 else "AI Code Review Complete",
                    event="COMMENT",
                    comments=batch,
                    commit=head_commit
                )

            # Record posted suggestions for acceptance-rate tracking
            posted = []
            for c in all_comments:
                line = c.get('line')
                start_line = c.get('start_line')
                if start_line:
                    posted.append({
                        "repository": repo_name,
                        "prNumber": pr_number,
                        "file": c['path'],
                        "line": line,
                        "startLine": start_line,
                        "endLine": line,
                    })
                else:
                    posted.append({
                        "repository": repo_name,
                        "prNumber": pr_number,
                        "file": c['path'],
                        "line": line,
                    })
            record_suggestions(posted)
            logger.info(f"Submitted review with {len(all_comments)} comments")
        else:
            pr.create_issue_comment("AI Code Review Complete - No issues found! Great job!")
            logger.info("No issues found in PR")
        
        # Record analytics
        response_time = time.time() - start_time
        record_review(repo_name, pr_number, issues_count, response_time)
            
    except Exception as e:
        logger.error(f"Error processing PR: {e}", exc_info=True)
        try:
            if gh:
                repo = gh.get_repo(repo_name)
                pr = repo.get_pull(pr_number)
                pr.create_issue_comment(
                    f"AI Code Review failed: {str(e)}\n\nPlease check the logs or try again."
                )
        except:
            pass