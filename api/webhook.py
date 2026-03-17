"""
api/webhook.py — Producer (Webhook) Serverless Function
========================================================
Responsibilities:
  • GET  /webhook — Facebook verification challenge
  • POST /webhook — Receive message event, validate HMAC, deduplicate, enqueue, return 200 OK

This function NEVER calls the Send API. It is the producer in the async workflow.
"""

import sys
import os

# Make `src` importable from inside the Vercel serverless sandbox
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
import hmac
import json
import traceback

from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

load_dotenv()

from src.services.db_service import is_duplicate, enqueue_message

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _verify_hmac(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Verify that the request really came from Facebook using the App Secret.
    SHA-1 HMAC — Facebook sends: 'sha1=<hex_digest>'
    If APP_SECRET is not set we skip verification (development convenience).
    """
    app_secret = os.getenv("APP_SECRET")
    if not app_secret:
        print("⚠️  APP_SECRET not set — skipping HMAC verification")
        return True

    if not signature_header or not signature_header.startswith("sha1="):
        print("❌ Missing or malformed X-Hub-Signature header")
        return False

    expected_sig = signature_header[5:]  # strip 'sha1='
    computed_sig = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha1
    ).hexdigest()

    return hmac.compare_digest(computed_sig, expected_sig)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Facebook webhook verification (GET)."""
    verify_token = os.getenv("VERIFY_TOKEN")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        print("✅ Webhook verified by Facebook")
        return PlainTextResponse(hub_challenge, status_code=200)
    print("❌ Webhook verification failed")
    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/")
@app.post("/webhook")
async def webhook(request: Request):
    """
    Receive a Messenger event from Facebook.
    1. Validate HMAC signature
    2. Deduplicate by mid
    3. Enqueue (status='pending')
    4. Return 200 OK immediately — never waits for Send API
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature")

    # 1. HMAC verification
    if not _verify_hmac(raw_body, signature):
        return PlainTextResponse("Unauthorized", status_code=401)

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        return PlainTextResponse("Bad Request", status_code=400)

    if body.get("object") != "page":
        return PlainTextResponse("NOT_A_PAGE_EVENT", status_code=404)

    try:
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                sender_psid = event.get("sender", {}).get("id")
                message     = event.get("message", {})
                mid         = message.get("mid")
                text        = message.get("text")

                # Only process text messages with a valid mid
                if not sender_psid or not mid or not text:
                    continue

                # 2. Deduplication — if mid already exists, skip silently
                if is_duplicate(mid):
                    print(f"⏭️  Duplicate mid skipped: {mid}")
                    continue

                print(f"📩 Enqueuing: [{sender_psid}] mid={mid} text={text[:40]!r}")

                # 3. Enqueue with status='pending'
                enqueue_message(mid=mid, psid=sender_psid, text=text)

    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        traceback.print_exc()
        # Still return 200 — Facebook would retry endlessly on non-200

    # 4. Always return 200 immediately
    return PlainTextResponse("EVENT_RECEIVED", status_code=200)
