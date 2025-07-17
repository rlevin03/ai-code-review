from fastapi import APIRouter, Request, HTTPException, Header
from app.core.security import verify_webhook_signature
from app.services.github_service import handle_pull_request

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
        
