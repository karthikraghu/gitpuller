"""Learning SQLAlchemy ORM model."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Learning(Base):
    """
    SQLAlchemy model for learning entries.
    """
    __tablename__ = "learnings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String, nullable=False, index=True)
    repo = Column(String, nullable=False)
    technology = Column(String, nullable=False)
    concept = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Learning(id={self.id}, repo='{self.repo}', technology='{self.technology}')>"
