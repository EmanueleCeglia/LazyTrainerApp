import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import text
from sqlalchemy import create_engine


def db_call(where_clause: str) -> pd.DataFrame:
    load_dotenv() # Utile se vuoi poter sovrascrivere con un .env locale per sviluppo non Docker

    # Prioritizza DATABASE_URL se esiste (impostata da Docker Compose)
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Se DATABASE_URL usa postgresql:// (comune), SQLAlchemy potrebbe preferire postgresql+psycopg2://
        # Assicurati che il dialect sia corretto se necessario, es:
        if database_url.startswith("postgresql://"):
             database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        engine = create_engine(database_url, echo=False)
    else:
        # Fallback al metodo precedente se DATABASE_URL non è impostata
        # (utile per ambienti dove non vuoi usare DATABASE_URL)
        user     = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DB")
        host     = os.getenv("POSTGRES_HOST", "db") # Cambia default a 'db' per Docker se non usi DATABASE_URL
        port     = os.getenv("POSTGRES_PORT", 5432) # Rendi anche la porta configurabile
        
        if not all([user, password, database, host]):
            raise ValueError("Mancano le credenziali del database o l'host.")

        engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
            echo=False,
        )

    query = f"""SELECT * FROM exercises_view {where_clause};"""
    df = pd.read_sql(text(query), engine)
    return df