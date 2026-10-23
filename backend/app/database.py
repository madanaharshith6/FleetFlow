import os
import socket
import logging
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("fleetflow.database")

def get_normalized_database_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://fleetflow:fleetflow@localhost:5432/fleetflow"
    )

    # 1. Normalize Postgres driver scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # 2. Handle Render internal hostnames when cross-region or private DNS is unreachable
    try:
        parsed = urllib.parse.urlsplit(url)
        host = parsed.hostname
        if host and host.startswith("dpg-") and "." not in host:
            try:
                socket.gethostbyname(host)
            except Exception:
                # Internal hostname failed to resolve; attempt known Render external regional proxies
                regions = ["oregon", "frankfurt", "ohio", "singapore", "virginia"]
                for reg in regions:
                    candidate = f"{host}.{reg}-postgres.render.com"
                    try:
                        s = socket.socket()
                        s.settimeout(2)
                        s.connect((candidate, 5432))
                        s.close()
                        url = url.replace(host, candidate)
                        break
                    except Exception:
                        pass
    except Exception:
        pass

    if "render.com" in url and "sslmode" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"

    return url

DATABASE_URL = get_normalized_database_url()
PRIMARY_DATABASE_URL = DATABASE_URL
DB_CONNECTED = False
DB_MESSAGE = ""
DB_ENGINE_TYPE = "postgresql"

connect_args = {
    "connect_timeout": 5
}
if "sslmode=require" in DATABASE_URL or ("render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL):
    connect_args["sslmode"] = "require"

# Test primary database connectivity with fail-safe SQLite fallback
try:
    if "sqlite" in DATABASE_URL:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        DB_ENGINE_TYPE = "sqlite"
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args=connect_args
        )
    with engine.connect() as probe:
        probe.execute(text("SELECT 1"))
    DB_CONNECTED = True
    DB_MESSAGE = "Primary PostgreSQL connection active" if DB_ENGINE_TYPE == "postgresql" else "SQLite database active"
except Exception as exc:
    DB_MESSAGE = str(exc)
    logger.warning(f"Primary PostgreSQL connection failed: {exc}. Initializing local resilient SQLite fallback.")
    fallback_url = "sqlite:///./fleetflow_prod.db"
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False}
    )
    DATABASE_URL = fallback_url
    DB_ENGINE_TYPE = "sqlite_fallback"
    DB_CONNECTED = True
    DB_MESSAGE = f"SQLite fallback active (Primary database notice: {str(exc)})"

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
