from fastapi import APIRouter
from datetime import datetime
import os
from app.config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "services": {
            "github": "connected",
            "openai": "connected"
        }
    }

@router.get("/ready")
async def readiness_check():
    """Check if all services are ready"""
    private_key_path = settings.GITHUB_PRIVATE_KEY_PATH
    checks = {
        "github_key": os.path.exists(private_key_path) if private_key_path else False,
        "env_vars": all([
            os.getenv("GITHUB_APP_ID"),
            os.getenv("OPENAI_API_KEY")
        ])
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks
    }