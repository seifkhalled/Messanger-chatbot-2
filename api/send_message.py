"""
api/send_message.py — Consumer (Worker) Serverless Function
============================================================
Responsibilities:
  • POST /send — Protected endpoint. Fetches all pending messages, applies FSM,
                 sends replies via Send API, marks messages done/failed.

Trigger this endpoint from:
  - A Vercel Cron Job (e.g., every 1 minute): vercel.json `crons` field
  - An external scheduler (n8n, GitHub Actions, etc.)
  - Manually via curl/Postman for testing

Protected by X-Worker-Secret header (must match WORKER_SECRET env var).
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

import asyncio
from functools import partial

from src.services.db_service import (
    get_lead,
    save_lead,
    fetch_pending_messages,
    mark_message_done,
    mark_message_failed,
)
from src.services.chatbot_service import call_send_api
from src.fsm.state_machine import apply_fsm

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI()


# ── Auth helper ──────────────────────────────────────────────────────────────

def _is_authorized(request: Request) -> bool:
    """
    Check that the caller provided the correct worker secret.
    If WORKER_SECRET is not set, allow all (dev convenience).
    """
    worker_secret = os.getenv("WORKER_SECRET")
    if not worker_secret:
        print("⚠️  WORKER_SECRET not set — allowing unauthenticated access")
        return True
    return request.headers.get("X-Worker-Secret") == worker_secret


# ── Route ─────────────────────────────────────────────────────────────────────

@app.post("/")
@app.post("/send")
async def send_pending_messages(request: Request):
    """
    Worker endpoint — process all pending messages.
    For each message:
      1. Fetch lead state from DB
      2. Apply FSM to get next state + reply text
      3. Save updated lead state
      4. Send reply via Messenger Send API
      5. Mark message done (or failed on error)
    """
    if not _is_authorized(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    pending = fetch_pending_messages(limit=20)
    print(f"🔄 Worker: found {len(pending)} pending message(s)")

    results = {"processed": 0, "failed": 0, "skipped": 0}

    loop = asyncio.get_event_loop()

    for msg in pending:
        mid       = msg["mid"]
        psid      = msg["psid"]
        text      = msg["text"]

        try:
            # 1. Fetch current lead state (synchronous Supabase client → run in executor)
            lead = await loop.run_in_executor(None, get_lead, psid)

            print(f"🔄 FSM: [{psid}] state={( lead or {}).get('state', 'START')} | text={text[:30]!r}")

            # 2. Apply FSM — pure function, no I/O
            next_state, reply_text, update_data = apply_fsm(lead, text)

            # 3. Persist updated lead state
            if update_data:
                await loop.run_in_executor(
                    None,
                    partial(save_lead, psid=psid, **update_data)
                )

            # 4. Send the reply
            await call_send_api(psid, reply_text)

            # 5. Mark done
            await loop.run_in_executor(None, mark_message_done, mid)

            print(f"✅ Done: [{psid}] → {next_state}")
            results["processed"] += 1

        except Exception as e:
            print(f"❌ Error processing mid={mid}: {e}")
            traceback.print_exc()
            try:
                await loop.run_in_executor(None, mark_message_failed, mid)
            except Exception:
                pass
            results["failed"] += 1

    return JSONResponse({
        "status": "ok",
        "processed": results["processed"],
        "failed": results["failed"],
    }, status_code=200)
