"""CRUD operations for learning entries."""

import sqlite3
from typing import List, Optional
from app.models.learning import Learning


def create_learning(conn: sqlite3.Connection, learning: Learning) -> int:
    """
    Insert a new learning entry into the database.
    
    Args:
        conn: Database connection
        learning: Learning object to insert
        
    Returns:
        int: ID of the inserted row
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO learnings (date, repo, technology, concept) VALUES (?, ?, ?, ?)",
        (learning.date, learning.repo, learning.technology, learning.concept)
    )
    conn.commit()
    return cursor.lastrowid


def create_learning_batch(conn: sqlite3.Connection, learnings: List[dict]) -> int:
    """
    Insert multiple learning entries in a batch.
    
    Args:
        conn: Database connection
        learnings: List of dicts with keys: date, repo, technology, concept
        
    Returns:
        int: Number of rows inserted
    """
    if not learnings:
        return 0
    
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO learnings (date, repo, technology, concept) VALUES (?, ?, ?, ?)",
        [(item["date"], item["repo"], item["technology"], item["concept"]) for item in learnings]
    )
    conn.commit()
    return cursor.rowcount


def get_learning_by_id(conn: sqlite3.Connection, learning_id: int) -> Optional[Learning]:
    """
    Retrieve a single learning entry by ID.
    
    Args:
        conn: Database connection
        learning_id: ID of the learning entry
        
    Returns:
        Learning object or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM learnings WHERE id = ?", (learning_id,))
    row = cursor.fetchone()
    
    if row:
        return Learning(
            id=row["id"],
            date=row["date"],
            repo=row["repo"],
            technology=row["technology"],
            concept=row["concept"],
            created_at=row["created_at"]
        )
    return None


def get_all_learnings(conn: sqlite3.Connection, limit: int = 100) -> List[Learning]:
    """
    Retrieve all learning entries.
    
    Args:
        conn: Database connection
        limit: Maximum number of entries to return
        
    Returns:
        List of Learning objects
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM learnings ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    
    return [
        Learning(
            id=row["id"],
            date=row["date"],
            repo=row["repo"],
            technology=row["technology"],
            concept=row["concept"],
            created_at=row["created_at"]
        )
        for row in rows
    ]


def get_learnings_by_date(conn: sqlite3.Connection, date: str) -> List[Learning]:
    """
    Retrieve learning entries for a specific date.
    
    Args:
        conn: Database connection
        date: Date string in YYYY-MM-DD format
        
    Returns:
        List of Learning objects
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM learnings WHERE date = ? ORDER BY created_at DESC",
        (date,)
    )
    rows = cursor.fetchall()
    
    return [
        Learning(
            id=row["id"],
            date=row["date"],
            repo=row["repo"],
            technology=row["technology"],
            concept=row["concept"],
            created_at=row["created_at"]
        )
        for row in rows
    ]


def delete_learning(conn: sqlite3.Connection, learning_id: int) -> bool:
    """
    Delete a learning entry by ID.
    
    Args:
        conn: Database connection
        learning_id: ID of the learning entry to delete
        
    Returns:
        bool: True if deleted, False if not found
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM learnings WHERE id = ?", (learning_id,))
    conn.commit()
    return cursor.rowcount > 0
