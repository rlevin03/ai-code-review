import asyncio
import os
import json
from dotenv import load_dotenv

# Add parent directory to path
import sys
sys.path.append('..')

from app.core.github_client import github_client
from app.services.github_service import handle_pull_request

load_dotenv()

async def test_webhook():
    """Test the webhook flow with a mock payload"""
    
    # Create a test payload - UPDATE THESE VALUES
    payload = {
        "action": "opened",
        "installation": {
            "id": 76343030  # Your installation ID from the test above
        },
        "repository": {
            "full_name": "YOUR_USERNAME/YOUR_REPO"  # <-- UPDATE THIS
        },
        "pull_request": {
            "number": 1,  # <-- UPDATE THIS to a real PR number
            "title": "Test PR",
            "state": "open"
        }
    }
    
    print(f"Testing webhook flow with payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        await handle_pull_request(payload)
        print("✓ Webhook processing completed successfully!")
    except Exception as e:
        print(f"✗ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_webhook())