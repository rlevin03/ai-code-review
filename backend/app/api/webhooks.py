from fastapi import APIRouter, Request, HTTPException, Header
from app.core.security import verify_webhook_signature
from app.services.github_service import handle_pull_request
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/github")
async def github_webhook(
    request: Request, 
    x_github_event: Optional[str] = Header(None)
):
    """Handle GitHub webhook events"""
    
    body = await request.body()
    
    if not x_github_event:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")
    
    # Log the event type
    logger.info(f"Received GitHub event: {x_github_event}")
    
    payload = await request.json()
    
    # Handle different event types
    if x_github_event == "pull_request":
        if payload.get("action") in ["opened", "synchronize", "reopened"]:
            logger.info(f"Processing PR #{payload['pull_request']['number']} action: {payload['action']}")

            asyncio.create_task(handle_pull_request(payload))
            
    elif x_github_event == "ping":
        logger.info("Received ping event - webhook is connected!")
        return {"message": "pong"}
    
    return {"status": "accepted"}

@router.post("/github/test")
async def test_webhook(request: Request):
    """Test endpoint to see raw webhook data"""
    body = await request.body()
    headers = dict(request.headers)
    
    print("=== WEBHOOK RECEIVED ===")
    print(f"Headers: {headers}")
    print(f"Body: {body.decode()}")
    print("=======================")
    
    return {"status": "test received"}
        
