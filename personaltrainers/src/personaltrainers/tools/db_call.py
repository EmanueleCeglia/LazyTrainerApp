import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import text
from sqlalchemy import create_engine


def db_call(where_clause: str) -> pd.DataFrame:
    # ------------------------------------------------------------------
    # 1) Load database credentials from .env
    # ------------------------------------------------------------------
    load_dotenv()  # this reads .env placed in project root

    user     = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    host     = os.getenv("POSTGRES_HOST", "localhost")  # default to localhost
    port     = 5432                                     # change if you mapped a different port

    # ------------------------------------------------------------------
    # 2) Create SQLAlchemy engine (psycopg2 is used under the hood)
    # ------------------------------------------------------------------
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
        echo=False,          # set True if you want to log every SQL statement
    )

    # ------------------------------------------------------------------
    # 3) Write the query (triple-quoted string is handy for multiline SQL)
    # ------------------------------------------------------------------
    query = f"""SELECT * FROM exercises_view {where_clause};"""

    # ------------------------------------------------------------------
    # 4) Read the query directly into a pandas DataFrame
    # ------------------------------------------------------------------
    df = pd.read_sql(text(query), engine)

    return df