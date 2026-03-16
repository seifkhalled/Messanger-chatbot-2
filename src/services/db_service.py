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

def save_lead(psid: str, name: str = None, phone: str = None, state: str = None):
    try:
        supabase = get_db_client()
        data = {"psid": psid, "state": state}
        if name is not None:
            data["name"] = name
        if phone is not None:
            data["phone"] = phone

        supabase.table("leads") \
            .upsert(data, on_conflict="psid") \
            .execute()
        print(f"✅ Lead saved: {psid}")
    except Exception as e:
        print(f"❌ DB Write Error: {e}")
        traceback.print_exc()
