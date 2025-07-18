from fastapi import APIRouter
from typing import Dict
from datetime import datetime
import json
import os

router = APIRouter()

# Simple file-based storage for MVP (replace with database later)
ANALYTICS_FILE = "analytics_data.json"

def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    return {"reviews": [], "stats": {"total": 0, "issues_found": 0}}

def save_analytics(data):
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(data, f)

@router.get("/dashboard")
async def get_dashboard_data() -> Dict:
    """Get dashboard statistics"""
    data = load_analytics()
    
    # Calculate recent stats
    recent_reviews = data["reviews"][-10:]  # Last 10 reviews
    
    return {
        "stats": {
            "totalReviews": data["stats"]["total"],
            "issuesFound": data["stats"]["issues_found"],
            "avgResponseTime": 2.5  # Placeholder
        },
        "recentReviews": recent_reviews
    }

def record_review(repository: str, pr_number: int, issues_found: int, response_time: float = 0):
    """Record a completed review"""
    data = load_analytics()
    
    review = {
        "repository": repository,
        "prNumber": pr_number,
        "issuesFound": issues_found,
        "responseTime": response_time,
        "timestamp": datetime.now().isoformat()
    }
    
    data["reviews"].append(review)
    data["stats"]["total"] += 1
    data["stats"]["issues_found"] += issues_found
    
    save_analytics(data)