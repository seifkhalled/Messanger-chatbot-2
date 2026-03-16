import requests, os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv("PAGE_ACCESS_TOKEN")
print(f"Token: {'✅ Loaded' if token else '❌ MISSING'}")

if token:
    response = requests.get(
        "https://graph.facebook.com/v21.0/me",
        params={"access_token": token}
    )
    data = response.json()
    if "error" in data:
        print(f"❌ Token invalid: {data['error']['message']}")
    else:
        print(f"✅ Token valid!")
        print(f"   Page: {data.get('name')}")
        print(f"   ID:   {data.get('id')}")
else:
    print("❌ No token found in .env")
