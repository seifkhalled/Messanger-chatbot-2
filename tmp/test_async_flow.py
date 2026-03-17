
import os
import sys
import json
import httpx
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

async def test_full_async_flow():
    """
    Integration Test:
    1. Send a 'message' to the Webhook (Producer)
    2. Verify it's in the DB as 'pending' (manually check via code)
    3. Call the Worker (Consumer)
    4. Verify the reply was 'sent' (mocked/logged) and DB status is 'done'
    """
    
    # We'll use the secret for the worker
    worker_secret = os.getenv("WORKER_SECRET", "test-secret")
    os.environ["WORKER_SECRET"] = worker_secret
    
    # Fake message data
    fake_mid = f"mid.test_{int(asyncio.get_event_loop().time())}"
    fake_psid = "user_12345"
    fake_text = "My name is Seif"
    
    print(f"--- Step 1: Simulating Webhook POST (Producer) ---")
    webhook_payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": fake_psid},
                "message": {"mid": fake_mid, "text": fake_text}
            }]
        }]
    }
    
    # Note: We import the FastAPI apps directly to test without a running server if needed,
    # but using a client is cleaner.
    from api.webhook import app as webhook_app
    from api.send_message import app as worker_app
    
    async with httpx.AsyncClient(app=webhook_app, base_url="http://testserver") as client:
        response = await client.post("/webhook", json=webhook_payload)
        print(f"Webhook Status: {response.status_code}")
        print(f"Webhook Body: {response.text}")
        assert response.status_code == 200

    print(f"\n--- Step 2: Verifying Pending Entry in DB ---")
    from src.services.db_service import fetch_pending_messages
    pending = fetch_pending_messages()
    found = any(m["mid"] == fake_mid for m in pending)
    print(f"Message found in 'pending' queue: {'✅' if found else '❌'}")
    assert found

    print(f"\n--- Step 3: Triggering Worker (Consumer) ---")
    async with httpx.AsyncClient(app=worker_app, base_url="http://testserver") as client:
        response = await client.post("/send", headers={"X-Worker-Secret": worker_secret})
        print(f"Worker Status: {response.status_code}")
        print(f"Worker Body: {response.json()}")
        assert response.status_code == 200
        assert response.json()["processed"] >= 1

    print(f"\n--- Step 4: Verifying Final DB Status & Lead State ---")
    from src.services.db_service import get_lead, is_duplicate
    # Double check lead state
    lead = get_lead(fake_psid)
    print(f"Lead State: {lead.get('state')}")
    print(f"Lead Name: {lead.get('name')}")
    
    # Verify no longer in pending (done)
    pending_after = fetch_pending_messages()
    still_pending = any(m["mid"] == fake_mid for m in pending_after)
    print(f"Message still pending: {'❌' if not still_pending else '✅'}")
    assert not still_pending
    
    print("\n🎉 Full Async Flow Integration Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_full_async_flow())
