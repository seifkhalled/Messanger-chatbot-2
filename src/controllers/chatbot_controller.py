from src.services.db_service import get_lead, save_lead
from src.services.chatbot_service import call_send_api

async def handle_message(sender_psid, text):
    try:
        lead = get_lead(sender_psid)
        
        # STATE 1 — get_lead returns None (new user)
        if not lead:
            save_lead(psid=sender_psid, state="ASKED_NAME")
            await call_send_api(sender_psid, "Hello! 👋 What's your name?")
            return

        state = lead.get("state")

        # STATE 2 — lead["state"] == "ASKED_NAME"
        if state == "ASKED_NAME":
            save_lead(psid=sender_psid, name=text, state="ASKED_PHONE")
            await call_send_api(sender_psid, f"Nice to meet you, {text}! What's your phone number?")
            return

        # STATE 3 — lead["state"] == "ASKED_PHONE"
        if state == "ASKED_PHONE":
            # Pass existing name to maintain it during upsert
            save_lead(psid=sender_psid, name=lead.get("name"), phone=text, state="COMPLETED")
            await call_send_api(sender_psid, "Thank you! ✅ Our team will contact you soon.")
            return

        # STATE 4 — lead["state"] == "COMPLETED"
        if state == "COMPLETED":
            await call_send_api(sender_psid, "We already have your details. Our team will reach out shortly!")
            return

    except Exception as e:
        print(f"❌ Handing Message Error: {e}")
