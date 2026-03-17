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

def is_message_processed(mid: str):
    """Check if a message ID has already been processed to prevent duplicates."""
    try:
        supabase = get_db_client()
        response = supabase.table("processed_messages") \
            .select("mid") \
            .eq("mid", mid) \
            .execute()
        return len(response.data) > 0
    except Exception as e:
        # If table doesn't exist, we might want to log it but continue
        print(f"⚠️ Deduplication check failed (maybe table missing?): {e}")
        return False

def log_message(mid: str, psid: str, text: str):
    """Log an incoming message for idempotency."""
    try:
        supabase = get_db_client()
        supabase.table("processed_messages").insert({
            "mid": mid,
            "psid": psid,
            "text": text
        }).execute()
    except Exception as e:
        print(f"❌ Error logging message: {e}")

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
