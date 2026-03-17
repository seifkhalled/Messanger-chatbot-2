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
    """
    Handle POST events from Facebook Messenger.
    Responds immediately with 200 OK to satisfy Facebook's timeout requirements.
    Processing happens asynchronously.
    """
    try:
        body = await request.json()
        if body.get("object") != "page":
            return PlainTextResponse("NOT_A_PAGE_EVENT", status_code=404)

        for entry in body.get("entry", []):
            messaging = entry.get("messaging", [])
            for event in messaging:
                sender_psid = event.get("sender", {}).get("id")
                message = event.get("message", {})
                
                # Extract text and ignore non-text messages for now
                text = message.get("text")
                if not sender_psid or not text:
                    continue

                print(f"📩 Received: [{sender_psid}] {text}")

                # Process message asynchronously: Fire and forget locally
                # Vercel's execution ends when we return, but we await the handle_message
                # for now to ensure it completes before the function instance potentially sleeps.
                # However, for 200 OK reliability, we must be fast.
                await handle_message(sender_psid, text)

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)

    except Exception as e:
        print(f"❌ Webhook Critical Error: {e}")
        traceback.print_exc()
        # Still return 200 to avoid Facebook retrying a failed webhook indefinitely
        return PlainTextResponse("EVENT_RECEIVED", status_code=200)
