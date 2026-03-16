import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
print(f"PAGE_ACCESS_TOKEN: {'✅ Loaded' if TOKEN else '❌ MISSING'}")

async def call_send_api(sender_psid, message_text):
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
    
    print(f"📤 Attempting to send message to: {sender_psid}")
    print(f"🔑 Token loaded: {'✅' if PAGE_ACCESS_TOKEN else '❌ MISSING'}")
    print(f"📝 Message: {message_text}")
    
    # Token MUST be in URL query string, not headers
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": sender_psid},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
        data = response.json()
        
        print(f"📡 Facebook API Response: {data}")
        
        if "error" in data:
            print(f"❌ Unable to send message: {data['error'].get('message', 'Unknown error')}")
        else:
            print(f"✅ Message sent to {sender_psid}")
            print(f"   Message ID: {data.get('message_id')}")
            
    except Exception as e:
        print(f"❌ Network Error: {e}")
