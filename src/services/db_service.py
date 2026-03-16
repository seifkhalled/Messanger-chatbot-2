import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SECRET_KEY")

print(f"SUPABASE_URL: {'✅ Loaded' if SUPABASE_URL else '❌ MISSING'}")
print(f"SUPABASE_KEY: {'✅ Loaded' if SUPABASE_KEY else '❌ MISSING'}")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("❌ Missing Supabase environment variables.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_lead(psid: str):
    try:
        response = supabase.table("leads") \
            .select("*") \
            .eq("psid", psid) \
            .single() \
            .execute()
        return response.data
    except Exception as e:
        # Supabase returns 406 or similar if single() finds no rows, which is fine
        if "NGRX" in str(e) or "PGRST116" in str(e): # Common codes for no rows
            return None
        print(f"❌ DB Read Error: {e}")
        return None

def save_lead(psid: str, name: str = None, 
              phone: str = None, state: str = None):
    try:
        data = {
            "psid": psid,
            "state": state
        }
        if name: data["name"] = name
        if phone: data["phone"] = phone

        supabase.table("leads") \
            .upsert(data, on_conflict="psid") \
            .execute()
        print(f"✅ Lead saved: {psid}")
    except Exception as e:
        print(f"❌ DB Write Error: {e}")
