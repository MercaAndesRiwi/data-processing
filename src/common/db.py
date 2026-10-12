"""Single database engine factory.

New code imports from here. The legacy
``src.simulators.pos_seed.connection.get_engine`` is left untouched
so existing ingestion scripts keep working.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def get_engine() -> Engine:
    """Create a SQLAlchemy engine from environment variables."""
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("POS_DB_USER"),
        password=os.getenv("POS_DB_PASSWORD"),
        host=os.getenv("POS_DB_HOST", "localhost"),
        port=int(os.getenv("POS_DB_PORT", "5432")),
        database=os.getenv("POS_DB_NAME"),
    )
    return create_engine(database_url)
