"""
Database Engine and Session Configuration.
Supports PostgreSQL for containerized / production deployments and SQLite for seamless zero-config local testing.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for obtaining a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
