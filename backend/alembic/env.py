from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database import Base
from app import models

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

def clean_db_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def run_migrations_offline():
    url = clean_db_url(os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url")))
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    section = config.get_section(config.config_ini_section)
    section["sqlalchemy.url"] = clean_db_url(os.getenv("DATABASE_URL", section["sqlalchemy.url"]))
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
