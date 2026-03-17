import os
import traceback
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def get_db_client():
    """Create a fresh Supabase client using env vars loaded at call time."""
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SECRET_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise Exception("❌ Missing Supabase environment variables.")

    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_lead(psid: str):
    try:
        supabase = get_db_client()
        response = supabase.table("leads") \
            .select("*") \
            .eq("psid", psid) \
            .single() \
            .execute()
        return response.data
    except Exception as e:
        error_str = str(e)
        # Supabase returns PGRST116 when single() finds no rows — that's expected
        if "PGRST116" in error_str or "NGRX" in error_str:
            return None
        print(f"❌ DB Read Error: {e}")
        traceback.print_exc()
        return None

def is_duplicate(mid: str) -> bool:
    """Return True if this mid already exists (any status). Prevents double-processing."""
    try:
        supabase = get_db_client()
        response = supabase.table("processed_messages") \
            .select("mid") \
            .eq("mid", mid) \
            .execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"⚠️ Deduplication check failed: {e}")
        return False

def enqueue_message(mid: str, psid: str, text: str) -> None:
    """Insert a new pending message into the queue. Call ONLY after is_duplicate() returns False."""
    try:
        supabase = get_db_client()
        supabase.table("processed_messages").insert({
            "mid": mid,
            "psid": psid,
            "text": text,
            "status": "pending"
        }).execute()
        print(f"📥 Enqueued: {mid}")
    except Exception as e:
        print(f"❌ Error enqueuing message: {e}")
        traceback.print_exc()

def fetch_pending_messages(limit: int = 20) -> list:
    """Fetch up to `limit` messages with status='pending' for the worker to process."""
    try:
        supabase = get_db_client()
        response = supabase.table("processed_messages") \
            .select("*") \
            .eq("status", "pending") \
            .limit(limit) \
            .execute()
        return response.data or []
    except Exception as e:
        print(f"❌ Error fetching pending messages: {e}")
        return []

def mark_message_done(mid: str) -> None:
    """Mark a message as successfully processed."""
    try:
        supabase = get_db_client()
        supabase.table("processed_messages") \
            .update({"status": "done"}) \
            .eq("mid", mid) \
            .execute()
    except Exception as e:
        print(f"❌ Error marking done [{mid}]: {e}")

def mark_message_failed(mid: str) -> None:
    """Mark a message as failed so it can be retried or inspected."""
    try:
        supabase = get_db_client()
        supabase.table("processed_messages") \
            .update({"status": "failed"}) \
            .eq("mid", mid) \
            .execute()
    except Exception as e:
        print(f"❌ Error marking failed [{mid}]: {e}")

from typing import Optional

def save_lead(psid: str, name: Optional[str] = None, phone: Optional[str] = None, state: Optional[str] = None):
    try:
        supabase = get_db_client()
        data = {"psid": psid}
        if state is not None:
            data["state"] = state
        if name is not None:
            data["name"] = name
        if phone is not None:
            data["phone"] = phone

        supabase.table("leads") \
            .upsert(data, on_conflict="psid") \
            .execute()
        print(f"✅ Lead saved: {psid} (State: {state})")
    except Exception as e:
        print(f"❌ DB Write Error: {e}")
        traceback.print_exc()
