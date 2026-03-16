import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
print(f"PAGE_ACCESS_TOKEN: {'✅ Loaded' if TOKEN else '❌ MISSING'}")

async def call_send_api(sender_psid, message_text):
    try:
        # Token MUST be in URL query string, not headers
        url = f"https://graph.facebook.com/v21.0/me/messages?access_token={TOKEN}"
        
        payload = {
            "recipient": {"id": sender_psid},
            "message": {"text": message_text},
            "messaging_type": "RESPONSE"
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if "error" in data:
            print(f"❌ Messenger API Error: {data['error'].get('message', 'Unknown error')}")
        else:
            print(f"✅ Message sent to {sender_psid}")
            
    except Exception as e:
        print(f"❌ Network Error: {e}")
