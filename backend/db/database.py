"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from typing import Generator

from db.models import Base

# Database file location
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "radikal.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL debug logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at: {DB_PATH}")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Analysis).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_db():
    """
    Drop all tables and recreate them.
    ⚠️ WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("⚠️ Database reset - all data deleted!")
