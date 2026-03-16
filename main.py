from fastapi import FastAPI
from dotenv import load_dotenv
from src.routes.routes import router
import uvicorn

load_dotenv()

app = FastAPI()
app.include_router(router)

@app.get("/debug")
async def debug():
    import os
    token = os.getenv("PAGE_ACCESS_TOKEN")
    return {
        "PAGE_ACCESS_TOKEN": (str(token)[:20] + "...") if token else "❌ MISSING",
        "SUPABASE_URL": "✅" if os.getenv("SUPABASE_URL") else "❌ MISSING",
        "SUPABASE_KEY": "✅" if os.getenv("SUPABASE_KEY") else "❌ MISSING",
        "VERIFY_TOKEN": "✅" if os.getenv("VERIFY_TOKEN") else "❌ MISSING"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
