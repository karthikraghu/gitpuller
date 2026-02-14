"""Database base configuration and table creation."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from app.core.config import settings

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
    from app.models.learning import Learning  # noqa
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {settings.DATABASE_PATH}")
