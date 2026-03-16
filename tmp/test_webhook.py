import requests

URL = "http://localhost:3000/webhook"
PSID = "test_user_psid_123456"

def send(text, expected_state):
    payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": PSID},
                "message": {"text": text}
            }]
        }]
    }
    try:
        response = requests.post(URL, json=payload)
        print(f"Expected: {expected_state}")
        print(f"Sent: '{text}' → Server: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Request Error: {e}")
    print("---")

print("Starting Lead Collection Test...\n")
send("Hello",          "STATE 1 - Ask Name")
send("John Doe",       "STATE 2 - Save Name, Ask Phone")
send("0612345678",     "STATE 3 - Save Phone, Complete")
send("Are you there?", "STATE 4 - Already Completed")
