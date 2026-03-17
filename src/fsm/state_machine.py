"""
Finite State Machine (FSM) for the Messenger Lead Bot.

Pure logic — no I/O, no DB, no HTTP. 
Given the current lead dict and the incoming text, returns:
    (next_state: str, reply_text: str, update_data: dict)
"""

from typing import Optional


# ── State constants ──────────────────────────────────────────────────────────
START       = "START"
ASKED_NAME  = "ASKED_NAME"
ASKED_PHONE = "ASKED_PHONE"
COMPLETED   = "COMPLETED"

ALL_STATES = {START, ASKED_NAME, ASKED_PHONE, COMPLETED}


def apply_fsm(lead: Optional[dict], incoming_text: str) -> tuple[str, str, dict]:
    """
    Apply FSM transition.

    Args:
        lead: Current lead row from the DB (or None if first contact).
        incoming_text: The raw text the user sent.

    Returns:
        A tuple of (next_state, reply_text, update_data).
        `update_data` is the partial dict suitable for save_lead().
    """
    current_state = (lead.get("state") or START) if lead else START

    if current_state == START:
        next_state  = ASKED_NAME
        reply_text  = "Hello! 👋 What's your name?"
        update_data = {"state": next_state}

    elif current_state == ASKED_NAME:
        name        = incoming_text.strip()
        next_state  = ASKED_PHONE
        reply_text  = f"Nice to meet you, {name}! 😊 What's your phone number?"
        update_data = {"state": next_state, "name": name}

    elif current_state == ASKED_PHONE:
        phone       = incoming_text.strip()
        name        = (lead or {}).get("name", "")
        next_state  = COMPLETED
        reply_text  = "Thank you! ✅ Your info is saved. Our team will be in touch soon."
        update_data = {"state": next_state, "phone": phone, "name": name}

    elif current_state == COMPLETED:
        # Self-loop — already collected
        next_state  = COMPLETED
        reply_text  = "We already have your details! 🚀 Our team will reach out to you soon."
        update_data = {}

    else:
        # Unknown / corrupted state — reset gracefully
        next_state  = ASKED_NAME
        reply_text  = "Hello! 👋 What's your name?"
        update_data = {"state": next_state}

    return next_state, reply_text, update_data
