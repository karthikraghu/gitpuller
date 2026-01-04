"""Learning data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Learning:
    """
    Represents a single learning entry.
    """
    repo: str
    technology: str
    concept: str
    date: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "date": self.date,
            "repo": self.repo,
            "technology": self.technology,
            "concept": self.concept,
            "created_at": str(self.created_at) if self.created_at else None
        }
