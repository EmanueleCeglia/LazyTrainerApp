# file: app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # carica .env anche quando sei fuori da Docker

# ➊ prova a leggere DATABASE_URL già completo
DATABASE_URL = os.getenv("DATABASE_URL")

# ➋ altrimenti, costruiscilo dai tre pezzi
if not DATABASE_URL:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    dbname = os.getenv("POSTGRES_DB", "postgres")

    # se il codice gira fuori dai container usiamo localhost
    host = os.getenv("POSTGRES_HOST", "localhost")  # opzionale

    DATABASE_URL = f"postgresql://{user}:{password}@{host}:5432/{dbname}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
