"""Database initialization and table creation."""

import sqlite3
from app.core.config import settings


def init_database():
    """
    Initialize the database and create all necessary tables.
    This function is idempotent - safe to call multiple times.
    """
    conn = sqlite3.connect(settings.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create learnings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            repo TEXT NOT NULL,
            technology TEXT NOT NULL,
            concept TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized: {settings.DATABASE_PATH}")
