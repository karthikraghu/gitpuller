"""SQLite database session management."""

import sqlite3
from typing import Generator
from app.core.config import settings


def get_db_connection():
    """
    Create and return a new SQLite database connection.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn


def get_db() -> Generator:
    """
    Dependency that provides a database connection.
    Automatically closes the connection when done.
    
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
