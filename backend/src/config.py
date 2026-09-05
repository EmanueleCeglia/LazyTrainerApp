"""
Central place for every environment-driven setting.

Importing this module loads the .env file, so any module can just do
`from src.config import DATABASE_URL` without worrying about load order.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:password@localhost:5432/postgres"
)

# Set SQL_ECHO=true in .env to dump every SQL statement to the console.
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")

# --- AI Provider ---
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-5.4-mini")

# --- Auth ---
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-lazytrainer-replace-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))  # 7 days
