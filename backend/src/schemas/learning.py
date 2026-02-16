"""Pydantic schemas for data validation.

These schemas serve two purposes:
1. API layer: FastAPI uses them to validate HTTP requests/responses
2. AI layer: LangChain uses LearningAnalysis to force Gemini to return structured data
"""

from pydantic import BaseModel, Field
from typing import List, Optional
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


# ---------------------------------------------------------------------------
# AI-specific schema — this is what .with_structured_output() validates against
# ---------------------------------------------------------------------------
class LearningAnalysis(BaseModel):
    """
    Wrapper schema that Gemini must conform to.
    
    Why a wrapper? .with_structured_output() needs a single Pydantic model.
    The LLM will return this object, and LangChain will auto-parse it.
    If Gemini returns bad data, LangChain raises a validation error
    instead of silently passing garbage to your database.
    """
    learnings: List[LearningCreate] = Field(
        default_factory=list,
        description="List of learning concepts extracted from the code changes"
    )


# ---------------------------------------------------------------------------
# API response schema — what the /api/sync endpoint returns
# ---------------------------------------------------------------------------
class SyncResponse(BaseModel):
    """Response from the POST /api/sync endpoint."""
    message: str = Field(..., description="Human-readable status message")
    count: int = Field(..., description="Number of learning items saved")
    items: List[LearningResponse] = Field(
        default_factory=list,
        description="The learning items that were saved"
    )
