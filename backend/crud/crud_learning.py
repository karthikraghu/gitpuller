"""CRUD operations for learning entries using SQLAlchemy ORM."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.learning import Learning
from app.schemas.learning import LearningCreate


def create_learning(db: Session, learning: LearningCreate) -> Learning:
    """
    Insert a new learning entry into the database.
    
    Args:
        db: Database session
        learning: LearningCreate schema object
        
    Returns:
        Learning: Created Learning ORM object
    """
    db_learning = Learning(
        date=learning.date,
        repo=learning.repo,
        technology=learning.technology,
        concept=learning.concept
    )
    db.add(db_learning)
    db.commit()
    db.refresh(db_learning)
    return db_learning


def create_learning_batch(db: Session, learnings: List[dict]) -> int:
    """
    Insert multiple learning entries in a batch.
    
    Args:
        db: Database session
        learnings: List of dicts with keys: date, repo, technology, concept
        
    Returns:
        int: Number of rows inserted
    """
    if not learnings:
        return 0
    
    db_learnings = [
        Learning(
            date=item["date"],
            repo=item["repo"],
            technology=item["technology"],
            concept=item["concept"]
        )
        for item in learnings
    ]
    
    db.bulk_save_objects(db_learnings)
    db.commit()
    return len(db_learnings)


def get_learning_by_id(db: Session, learning_id: int) -> Optional[Learning]:
    """
    Retrieve a single learning entry by ID.
    
    Args:
        db: Database session
        learning_id: ID of the learning entry
        
    Returns:
        Learning object or None if not found
    """
    return db.query(Learning).filter(Learning.id == learning_id).first()


def get_all_learnings(db: Session, skip: int = 0, limit: int = 100) -> List[Learning]:
    """
    Retrieve all learning entries with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of entries to return
        
    Returns:
        List of Learning objects
    """
    return db.query(Learning).order_by(Learning.created_at.desc()).offset(skip).limit(limit).all()


def get_learnings_by_date(db: Session, date: str) -> List[Learning]:
    """
    Retrieve learning entries for a specific date.
    
    Args:
        db: Database session
        date: Date string in YYYY-MM-DD format
        
    Returns:
        List of Learning objects
    """
    return db.query(Learning).filter(Learning.date == date).order_by(Learning.created_at.desc()).all()


def get_learnings_by_repo(db: Session, repo: str) -> List[Learning]:
    """
    Retrieve learning entries for a specific repository.
    
    Args:
        db: Database session
        repo: Repository name
        
    Returns:
        List of Learning objects
    """
    return db.query(Learning).filter(Learning.repo == repo).order_by(Learning.created_at.desc()).all()


def delete_learning(db: Session, learning_id: int) -> bool:
    """
    Delete a learning entry by ID.
    
    Args:
        db: Database session
        learning_id: ID of the learning entry to delete
        
    Returns:
        bool: True if deleted, False if not found
    """
    db_learning = db.query(Learning).filter(Learning.id == learning_id).first()
    if db_learning:
        db.delete(db_learning)
        db.commit()
        return True
    return False
