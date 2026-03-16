import os
import traceback
from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse
from src.controllers.chatbot_controller import handle_message
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.get("/")
async def root():
    return PlainTextResponse("Messenger Webhook Server is running!")

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge, status_code=200)
    return PlainTextResponse("Forbidden", status_code=403)

@router.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
        if body.get("object") == "page":
            for entry in body.get("entry", []):
                messaging = entry.get("messaging", [])
                if not messaging:
                    continue

                event = messaging[0]
                sender_psid = event.get("sender", {}).get("id")
                if not sender_psid:
                    continue

                message = event.get("message", {})
                text = message.get("text")

                # Guard — ignore messages with no text
                if not text:
                    return PlainTextResponse("EVENT_RECEIVED", status_code=200)

                print(f"[{sender_psid}] Message: {text}")

                # CRITICAL: await handle_message BEFORE returning response
                await handle_message(sender_psid, text)

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        traceback.print_exc()
        return PlainTextResponse("ERROR", status_code=500)
