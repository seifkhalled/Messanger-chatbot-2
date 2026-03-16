import requests, os, sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

def test_full_flow():
    load_dotenv()
    verify_token = os.getenv("VERIFY_TOKEN")
    page_token = os.getenv("PAGE_ACCESS_TOKEN")
    
    BASE_URL = "http://localhost:3000"
    
    print("\n--- STEP 1: Test Server Running ---")
    try:
        res = requests.get(f"{BASE_URL}/")
        print(f"Status: {res.status_code} | Body: {res.text}")
        assert res.text == "Messenger Webhook Server is running!"
    except Exception as e:
        print(f"❌ Server not running? {e}")
        return

    print("\n--- STEP 2: Test Webhook Verification ---")
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": verify_token,
        "hub.challenge": "test123"
    }
    res = requests.get(f"{BASE_URL}/webhook", params=params)
    print(f"Status: {res.status_code} | Body: {res.text}")
    assert res.text == "test123"

    print("\n--- STEP 3: Test State Machine (PSID: test_user_123) ---")
    psid = "test_user_123"
    
    # 1. New User -> Ask Name
    print("Sending 'Hello'...")
    payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": psid},
                "message": {"text": "Hello"}
            }]
        }]
    }
    requests.post(f"{BASE_URL}/webhook", json=payload)

    # 2. State ASKED_NAME -> Ask Phone
    print("Sending 'John Doe'...")
    payload["entry"][0]["messaging"][0]["message"]["text"] = "John Doe"
    requests.post(f"{BASE_URL}/webhook", json=payload)

    # 3. State ASKED_PHONE -> Completed
    print("Sending '0612345678'...")
    payload["entry"][0]["messaging"][0]["message"]["text"] = "0612345678"
    requests.post(f"{BASE_URL}/webhook", json=payload)

    # 4. State COMPLETED -> Already Completed message
    print("Sending 'Are you there?'...")
    payload["entry"][0]["messaging"][0]["message"]["text"] = "Are you there?"
    requests.post(f"{BASE_URL}/webhook", json=payload)

    print("\n--- STEP 4: Test Database Integrity ---")
    from src.services.db_service import get_lead
    lead = get_lead(psid)
    if lead:
        print(f"✅ Lead found in DB: {lead}")
        assert lead["psid"] == psid
        assert lead["name"] == "John Doe"
        assert lead["phone"] == "0612345678"
        assert lead["state"] == "COMPLETED"
    else:
        print("❌ Lead NOT found in DB!")

    print("\n--- STEP 5: Test Real Messenger API ---")
    test_psid = "25899490533012994"
    if page_token:
        url = f"https://graph.facebook.com/v21.0/me/messages?access_token={page_token}"
        msg_payload = {
            "recipient": {"id": test_psid},
            "message": {"text": "Hello! This is a test message 👋"},
            "messaging_type": "RESPONSE"
        }
        res = requests.post(url, json=msg_payload)
        print(f"Status: {res.status_code} | Body: {res.text}")
        if res.status_code == 200:
            print("✅ Real message sent successfully!")
        else:
            print("❌ Failed to send real message.")

if __name__ == "__main__":
    test_full_flow()
