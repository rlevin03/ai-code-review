from fastapi import APIRouter, Request, HTTPException, Header
import hmac
import hashlib
from app.core.github_client import GitHubClient
from app.core.security import verify_webhook_signature


router = APIRouter()

@router.post("/github")
async def github_webhook(
    request: Request, 
    x_hub_signature: str = Header(None), 
    x_github_event: str = Header(None)
):
    """Handle GitHub webhook events"""
    
    body = await request.body()
    
    if not x_hub_signature or not x_github_event:
        raise HTTPException(status_code=400, detail="Missing headers")
    
    # Verify the signature
    if not verify_webhook_signature(body, x_hub_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    
    if x_github_event == "pull_request":
        if payload["action"] in ["opened", "synchronize", "reopened"]:
            await handle_pull_request(payload)
    
    return {"status": "ok"}
        
