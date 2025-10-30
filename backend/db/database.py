"""
Database connection and session management.
Supports both SQLite (local development) and Supabase (PostgreSQL).
"""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from db.models import Base

# Load environment variables from .env file
load_dotenv()

# Get database type from environment (default to supabase)
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "supabase").lower()

if DATABASE_TYPE == "supabase":
    # Use Supabase PostgreSQL database
    DATABASE_URL = os.getenv(
        "SUPABASE_DB_URL", 
        "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    )
    
    # Create engine for PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL debug logging
        pool_pre_ping=True,  # Test connections before using
        pool_size=10,
        max_overflow=20
    )
    
    print(f"✅ Using Supabase PostgreSQL database at: {DATABASE_URL.split('@')[1]}")
    
else:
    # Use SQLite for local development
    DB_DIR = Path(__file__).parent.parent / "data"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DB_DIR / "radikal.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    
    # Create engine for SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False  # Set to True for SQL debug logging
    )
    
    print(f"✅ Using SQLite database at: {DB_PATH}")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    Base.metadata.create_all(bind=engine)
    if DATABASE_TYPE == "supabase":
        print(f"✅ Database tables created/verified in Supabase PostgreSQL")
    else:
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
