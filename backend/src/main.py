from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from src.api.routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="LazyTrainer API",
    version="1.0.0"
)

# Connect the routes from the api folder
app.include_router(router)