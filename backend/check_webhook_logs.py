import os
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")

print("=== Webhook Configuration ===")
print(f"Webhook Secret Set: {'Yes' if webhook_secret else 'No'}")
print(f"Secret Length: {len(webhook_secret) if webhook_secret else 0}")

# Test signature verification
test_payload = b'{"test": "data"}'
test_signature = "sha256=" + hmac.new(
    webhook_secret.encode('utf-8'),
    test_payload,
    hashlib.sha256
).hexdigest()

print(f"\nTest Signature Generation:")
print(f"Payload: {test_payload}")
print(f"Generated Signature: {test_signature}")

# Also check ngrok
print("\n=== Ngrok Check ===")
print("Make sure ngrok is running and forwarding to port 8000")
print("Your webhook URL should be: https://YOUR-NGROK-URL.ngrok.io/api/webhooks/github")