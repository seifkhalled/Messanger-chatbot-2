import asyncio
from functools import partial
from src.services.db_service import get_lead, save_lead
from src.services.chatbot_service import call_send_api

async def handle_message(sender_psid, text):
    """
    Core conversation logic using a Finite State Machine (FSM).
    Determines the current state of the lead and decides the next question.
    """
    try:
        loop = asyncio.get_event_loop()
        
        # 1. Fetch current lead state
        lead = await loop.run_in_executor(None, get_lead, sender_psid)
        current_state = lead.get("state") if lead else "START"

        print(f"🔄 FSM: [{sender_psid}] State: {current_state} -> Input: {text[:20]}...")

        # 2. State Transition Logic
        if current_state == "START" or not current_state:
            # Transition: START -> ASKED_NAME
            await loop.run_in_executor(
                None,
                partial(save_lead, psid=sender_psid, state="ASKED_NAME")
            )
            await call_send_api(sender_psid, "Hello! 👋 I'm your automated assistant. What's your name?")

        elif current_state == "ASKED_NAME":
            # Transition: ASKED_NAME -> ASKED_PHONE
            await loop.run_in_executor(
                None,
                partial(save_lead, psid=sender_psid, name=text, state="ASKED_PHONE")
            )
            await call_send_api(
                sender_psid,
                f"Nice to meet you, {text}! 🤝 What's your phone number?"
            )

        elif current_state == "ASKED_PHONE":
            # Transition: ASKED_PHONE -> COMPLETED
            await loop.run_in_executor(
                None,
                partial(save_lead, psid=sender_psid,
                        name=lead.get("name"), phone=text, state="COMPLETED")
            )
            await call_send_api(
                sender_psid,
                "Thank you! ✅ I've saved your details. Our team will contact you soon."
            )

        elif current_state == "COMPLETED":
            # Transition: COMPLETED (Self-loop)
            await call_send_api(
                sender_psid,
                "We already have your details! 🚀 Our team is processing your request and will reach out shortly."
            )

    except Exception as e:
        print(f"❌ FSM Error: {e}")
        import traceback
        traceback.print_exc()
