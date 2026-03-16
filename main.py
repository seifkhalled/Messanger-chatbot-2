from fastapi import FastAPI
from dotenv import load_dotenv
from src.routes.routes import router
import uvicorn

load_dotenv()

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
