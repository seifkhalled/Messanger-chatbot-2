import os
import httpx
import traceback
from dotenv import load_dotenv

load_dotenv()

async def call_send_api(sender_psid, message_text):
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

    print(f"📤 Sending to: {sender_psid}")
    print(f"🔑 Token: {'✅' if PAGE_ACCESS_TOKEN else '❌ MISSING'}")

    if not PAGE_ACCESS_TOKEN:
        print("❌ Cannot send - token missing!")
        return

    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": sender_psid},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            data = response.json()

        print(f"📡 API Response: {data}")

        if "error" in data:
            print(f"❌ Send failed: {data['error']}")
        else:
            print(f"✅ Sent! Message ID: {data.get('message_id')}")

    except Exception as e:
        print(f"❌ Network Error: {e}")
        traceback.print_exc()
