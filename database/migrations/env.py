"""Alembic environment: URL comes from .env via src.common.db."""

import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

from alembic import context
from src.common.db import get_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Manual migrations: the five country schemas are cloned with a
# DO..FOREACH block, which autogenerate cannot model. Keep None.
target_metadata = None


def _override_url_from_env() -> None:
    url = (
        f"postgresql+psycopg://{os.getenv('POS_DB_USER')}:"
        f"{os.getenv('POS_DB_PASSWORD')}@"
        f"{os.getenv('POS_DB_HOST', 'localhost')}:"
        f"{os.getenv('POS_DB_PORT', '5432')}/"
        f"{os.getenv('POS_DB_NAME')}"
    )
    config.set_main_option("sqlalchemy.url", url)


def run_migrations_offline() -> None:
    _override_url_from_env()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
