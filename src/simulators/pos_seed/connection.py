import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def get_engine():
    """Create and return a SQLAlchemy engine."""
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("POS_DB_USER"),
        password=os.getenv("POS_DB_PASSWORD"),
        host=os.getenv("POS_DB_HOST", "localhost"),
        port=int(os.getenv("POS_DB_PORT", "5432")),
        database=os.getenv("POS_DB_NAME"),
    )

    return create_engine(database_url)


def test_connection():
    """Verify the PostgreSQL connection."""
    engine = get_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            print("Successful connection to PostgreSQL.")
            print(result.scalar())
    finally:
        engine.dispose()


if __name__ == "__main__":
    test_connection()
