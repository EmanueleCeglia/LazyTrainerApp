from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from src.api.routes import router
from src.api.auth_routes import router as auth_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="LazyTrainer API",
    version="1.0.0"
)

# Connect the routes from the api folder
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(router)