"""Database base configuration and table creation."""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from src.core.config import settings

# Ensure the database directory exists before SQLite tries to write to it.
# os.makedirs with exist_ok=True is idempotent — safe to call every time.
db_dir = Path(settings.DATABASE_PATH).parent
os.makedirs(db_dir, exist_ok=True)

# Create the SQLAlchemy engine
engine = create_engine(
    f"sqlite:///{settings.DATABASE_PATH}",
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True to see SQL queries in console
)

# Create declarative base for models
Base = declarative_base()


def init_database():
    """
    Initialize the database and create all tables.
    This function is idempotent - safe to call multiple times.
    """
    # Import all models here to ensure they're registered
    from src.models.learning import Learning  # noqa
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {settings.DATABASE_PATH}")

