from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from app.core.security import verify_webhook_signature
from app.services.github_service import handle_pull_request
import logging
import json
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/github")
async def github_webhook(
    request: Request, 
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None)
):
    """Handle GitHub webhook events"""
    
    # Get the raw body for signature verification
    body = await request.body()
    
    # Log the webhook receipt
    logger.info(f"=== WEBHOOK RECEIVED ===")
    logger.info(f"Event: {x_github_event}")
    logger.info(f"Signature provided: {bool(x_hub_signature_256)}")
    
    if not x_github_event:
        logger.error("Missing X-GitHub-Event header")
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")
    
    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Log what we received
    if x_github_event == "pull_request":
        pr_action = payload.get("action", "unknown")
        pr_number = payload.get("pull_request", {}).get("number", "unknown")
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        logger.info(f"PR Event: {pr_action} on PR #{pr_number} in {repo_name}")
    
    # For now, skip signature verification to test
    # TODO: Re-enable this after testing
    # if x_hub_signature_256:
    #     if not verify_webhook_signature(body, x_hub_signature_256):
    #         logger.error("Invalid webhook signature")
    #         raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Handle different event types
    if x_github_event == "pull_request":
        if payload.get("action") in ["opened", "synchronize", "reopened"]:
            logger.info(f"Processing PR #{payload['pull_request']['number']}")
            # Run async to return quickly to GitHub
            asyncio.create_task(handle_pull_request(payload))
            
    elif x_github_event == "ping":
        logger.info("Received ping event - webhook is connected!")
        return {"message": "pong", "zen": payload.get("zen")}
    
    logger.info("Webhook processed successfully")
    return {"status": "accepted"}

@router.post("/github/test")
async def test_webhook(request: Request):
    """Test endpoint to see raw webhook data"""
    body = await request.body()
    headers = dict(request.headers)
    
    print("=== TEST WEBHOOK RECEIVED ===")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Body: {body.decode()[:500]}...")
    print("=============================")
    
    return {"status": "test received", "headers_count": len(headers)}