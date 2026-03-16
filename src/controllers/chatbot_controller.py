import asyncio
from functools import partial
from src.services.db_service import get_lead, save_lead
from src.services.chatbot_service import call_send_api

async def handle_message(sender_psid, text):
    try:
        loop = asyncio.get_event_loop()

        # Run sync Supabase call in thread executor to avoid blocking event loop
        lead = await loop.run_in_executor(None, get_lead, sender_psid)

        # STATE 1 — New user
        if not lead:
            await loop.run_in_executor(
                None,
                partial(save_lead, psid=sender_psid, state="ASKED_NAME")
            )
            await call_send_api(sender_psid, "Hello! 👋 What's your name?")
            return

        state = lead.get("state")

        # STATE 2 — ASKED_NAME
        if state == "ASKED_NAME":
            await loop.run_in_executor(
                None,
                partial(save_lead, psid=sender_psid, name=text, state="ASKED_PHONE")
            )
            await call_send_api(
                sender_psid,
                f"Nice to meet you, {text}! What's your phone number?"
            )
            return

        # STATE 3 — ASKED_PHONE
        if state == "ASKED_PHONE":
            await loop.run_in_executor(
                None,
                partial(save_lead, psid=sender_psid,
                        name=lead.get("name"), phone=text, state="COMPLETED")
            )
            await call_send_api(
                sender_psid,
                "Thank you! ✅ Our team will contact you soon."
            )
            return

        # STATE 4 — COMPLETED
        if state == "COMPLETED":
            await call_send_api(
                sender_psid,
                "We already have your details. Our team will reach out shortly!"
            )
            return

    except Exception as e:
        print(f"❌ Handle Message Error: {e}")
        import traceback
        traceback.print_exc()
