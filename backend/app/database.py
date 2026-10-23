import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://fleetflow:fleetflow@localhost:5432/fleetflow"
)

# Render and cloud PostgreSQL providers provide URLs starting with postgres://
# SQLAlchemy 1.4+ and 2.0 require the dialect to be postgresql:// or postgresql+psycopg2://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

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
