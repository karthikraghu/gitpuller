"""Pydantic schemas for data validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LearningBase(BaseModel):
    """Base schema for Learning with common attributes."""
    repo: str = Field(..., description="Repository name")
    technology: str = Field(..., description="Technology or framework used")
    concept: str = Field(..., description="Learning concept identified")
    date: str = Field(..., description="Date in YYYY-MM-DD format")


class LearningCreate(LearningBase):
    """Schema for creating a new learning entry."""
    pass


class LearningResponse(LearningBase):
    """Schema for learning entry response (includes DB fields)."""
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Allows parsing from ORM objects
