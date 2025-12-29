from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. The URL (Same as in alembic.ini)
# In production, we will fetch this from a secure .env file
DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/postgres"

# 2. The Engine (The actual connection)
engine = create_engine(DATABASE_URL, echo=True)

# 3. The Session Factory (Creates a temporary workspace for each request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Dependency (This function is used by FastAPI to get a DB session)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()