"""Sync API router — triggers the GitHub → Gemini → Database pipeline.

This is the HTTP version of what main.py used to do via CLI.
The Next.js frontend will call POST /api/sync to trigger a sync.

KEY CONCEPT — FastAPI Dependency Injection:
  The `db: Session = Depends(get_db)` parameter tells FastAPI:
    1. Before handling the request, call get_db() to get a DB session
    2. Pass that session into the endpoint function
    3. After the response is sent, close the session automatically
  This means you never manually open/close DB sessions in endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.base import init_database
from src.crud.crud_learning import create_learning_batch
from src.services.github_service import fetch_recent_commits
from src.services.llm_service import analyze_commits_with_ai
from src.schemas.learning import SyncResponse, LearningResponse

logger = logging.getLogger(__name__)

# Create a router — this groups related endpoints together.
# The prefix means all routes here start with /api.
# Tags group endpoints in the Swagger docs UI.
router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync", response_model=SyncResponse)
def sync_learning(db: Session = Depends(get_db)):
    """
    Trigger a full sync: fetch GitHub commits → analyze with Gemini → save to DB.
    
    This is the main action endpoint. When the frontend clicks "Sync Now",
    it sends a POST here and gets back the newly discovered learning items.
    """
    # Ensure DB tables exist (idempotent — safe to call every time)
    init_database()

    # Step 1: Fetch recent commits from GitHub
    logger.info("Step 1: Fetching recent commits from GitHub...")
    push_data = fetch_recent_commits()

    if not push_data:
        return SyncResponse(
            message="No commits found in the last 24 hours.",
            count=0,
            items=[]
        )

    # Step 2: Analyze with Gemini AI (returns validated Pydantic objects)
    logger.info("Step 2: Analyzing commits with Gemini AI...")
    learning_items = analyze_commits_with_ai(push_data)

    if not learning_items:
        return SyncResponse(
            message="No meaningful learning concepts identified.",
            count=0,
            items=[]
        )

    # Step 3: Save to database
    logger.info("Step 3: Saving to database...")
    count = create_learning_batch(db, learning_items)

    # Step 4: Build response with saved items (including DB-generated IDs)
    # We re-query to get the created_at timestamps and IDs
    from src.crud.crud_learning import get_all_learnings
    saved = get_all_learnings(db, skip=0, limit=count)
    response_items = [LearningResponse.model_validate(item) for item in saved]

    return SyncResponse(
        message=f"Successfully synced {count} learning items.",
        count=count,
        items=response_items
    )
