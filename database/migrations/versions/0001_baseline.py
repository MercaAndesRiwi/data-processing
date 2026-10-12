"""Baseline: freeze the current pos schema.sql as revision 0001.

Upgrade replays database/schemas/pos/schema.sql (all statements use
IF NOT EXISTS, so it is safe on existing volumes). Seeds still run
after `alembic upgrade head`; this revision creates structure only.
"""

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema_file = (
        Path(__file__).resolve().parents[2] / "schemas" / "pos" / "schema.sql"
    )
    sql = schema_file.read_text(encoding="utf-8")
    # Raw cursor: the schema file uses plpgsql format() with %I, which
    # SQLAlchemy's driver-level execution would misread as placeholders.
    raw = op.get_bind().connection
    cursor = raw.cursor()
    cursor.execute(sql)
    cursor.close()


def downgrade() -> None:
    bind = op.get_bind()
    for schema in ("colombia", "peru", "ecuador", "bolivia", "chile"):
        bind.exec_driver_sql(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    bind.exec_driver_sql("DROP TABLE IF EXISTS public.promotions")
    bind.exec_driver_sql("DROP TABLE IF EXISTS public.exchange_rate")
    bind.exec_driver_sql("DROP TABLE IF EXISTS public.pos_seed_runs")
