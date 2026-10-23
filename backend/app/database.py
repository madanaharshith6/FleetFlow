import os
import socket
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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

    return url

DATABASE_URL = get_normalized_database_url()

connect_args = {
    "connect_timeout": 5
}
# Enforce SSL if specified in query string or when connecting to cloud host (e.g. Render)
if "sslmode=require" in DATABASE_URL or ("render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL):
    connect_args["sslmode"] = "require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args if "sqlite" not in DATABASE_URL else {}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
