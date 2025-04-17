# file: app/create_tables.py
from app.db import engine
from app.db_models import Base


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("✅  Tables created!")


if __name__ == "__main__":
    main()
