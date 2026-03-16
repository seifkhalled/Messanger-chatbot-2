import requests
import os
from dotenv import load_dotenv

load_dotenv()

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
TEST_PSID = "25899490533012994"

def test_token():
    print("\n🔍 Testing PAGE_ACCESS_TOKEN...\n")
    
    # Step 1 — Check token is loaded
    print(f"🔑 Token loaded: {'✅' if PAGE_ACCESS_TOKEN else '❌ MISSING'}")
    if PAGE_ACCESS_TOKEN:
        print(f"   Preview: {PAGE_ACCESS_TOKEN[:20]}...")
    
    # Step 2 — Verify token is valid
    print("\n📡 Verifying token with Facebook...")
    response = requests.get(
        "https://graph.facebook.com/v21.0/me",
        params={"access_token": PAGE_ACCESS_TOKEN}
    )
    data = response.json()
    
    if "error" in data:
        print(f"❌ Token invalid: {data['error']['message']}")
        return
    else:
        print(f"✅ Token valid!")
        print(f"   Page: {data.get('name')}")
        print(f"   ID:   {data.get('id')}")
    
    # Step 3 — Send real test message
    print(f"\n📤 Sending test message to PSID: {TEST_PSID}...")
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": TEST_PSID},
        "message": {"text": "🤖 Test message from bot - token is working!"},
        "messaging_type": "RESPONSE"
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if "error" in data:
        print(f"❌ Failed to send: {data['error']['message']}")
        print(f"   Code: {data['error']['code']}")
        print(f"   Type: {data['error']['type']}")
    else:
        print(f"✅ Message sent successfully!")
        print(f"   Message ID:   {data.get('message_id')}")
        print(f"   Recipient ID: {data.get('recipient_id')}")

if __name__ == "__main__":
    test_token()