from src.services.db_service import save_lead, get_lead
import time

def test_db():
    psid = "test_user_" + str(int(time.time()))
    print(f"Testing with PSID: {psid}")
    
    # Save a lead
    print("Saving lead...")
    save_lead(psid, "Test User", "1234567890", "initial")
    
    # Retrieve the lead
    print("Retrieving lead...")
    lead = get_lead(psid)
    if lead:
        print(f"✅ Success! Lead found: {lead}")
    else:
        print("❌ Error: Lead not found")

if __name__ == "__main__":
    test_db()
