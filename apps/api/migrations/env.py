"""Alembic ortamı — migration'lar owner rolüyle (MIGRATION_DATABASE_URL) çalışır."""

from alembic import context
from sqlalchemy import create_engine

from app.config import get_settings
from app.models import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    settings = get_settings()
    url = context.config.get_main_option("sqlalchemy.url") or settings.migration_database_url
    if not url:
        raise RuntimeError("MIGRATION_DATABASE_URL tanımlı değil")
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
