from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import DATABASE_URL, SQL_ECHO

# 1. The Engine (the actual connection). URL and echo come from .env — see src/config.py
engine = create_engine(DATABASE_URL, echo=SQL_ECHO, pool_pre_ping=True)

# 2. The Session Factory (Creates a temporary workspace for each request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Dependency (This function is used by FastAPI to get a DB session)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
