import hmac
import hashlib
from app.config import settings

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify the webhook is from GitHub"""
    if not signature:
        return False
    
    hash_object = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode('utf-8'), 
        msg=payload, 
        digestmod=hashlib.sha256
    )
    expected_signature = f"sha256={hash_object.hexdigest()}"
    return hmac.compare_digest(
        expected_signature, 
        signature
    )
