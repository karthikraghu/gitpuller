"""Sync API router — triggers the GitHub → LLM → Database pipeline.

This is the HTTP version of what main.py used to do via CLI.
The Next.js frontend will call POST /api/sync to trigger a sync.

KEY CONCEPT — FastAPI Dependency Injection:
  The `session: AsyncSession = Depends(get_db_session)` parameter tells FastAPI:
    1. Before handling the request, call get_db_session() to get a Neo4j session
    2. Pass that session into the endpoint function
    3. After the response is sent, close the session automatically
  This means you never manually open/close DB sessions in endpoints.

KEY CONCEPT — async def vs def:
  With Neo4j's async driver, our endpoints must be `async def`.
  This lets FastAPI handle them without blocking the event loop,
  meaning multiple requests can be served concurrently.
"""

import logging
from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from src.db.session import get_db_session
from src.crud.crud_learning import create_learning_batch, get_all_learnings
from src.services.github_service import fetch_recent_commits
from src.services.llm_service import analyze_commits_with_ai
from src.schemas.learning import SyncResponse, LearningResponse

logger = logging.getLogger(__name__)

# Create a router — this groups related endpoints together.
# The prefix means all routes here start with /api.
# Tags group endpoints in the Swagger docs UI.
router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync", response_model=SyncResponse)
async def sync_learning(session: AsyncSession = Depends(get_db_session)):
    """
    Trigger a full sync: fetch GitHub commits → analyze with LLM → save to DB.

    This is the main action endpoint. When the frontend clicks "Sync Now",
    it sends a POST here and gets back the newly discovered learning items.
    """
    # Step 1: Fetch recent commits from GitHub
    logger.info("Step 1: Fetching recent commits from GitHub...")
    push_data = fetch_recent_commits()

    if not push_data:
        return SyncResponse(
            message="No commits found in the last 24 hours.",
            count=0,
            items=[]
        )

    # Step 2: Analyze with LLM (returns validated Pydantic objects)
    logger.info("Step 2: Analyzing commits with LLM...")
    learning_items = analyze_commits_with_ai(push_data)

    if not learning_items:
        return SyncResponse(
            message="No meaningful learning concepts identified.",
            count=0,
            items=[]
        )

    # Step 3: Save to Neo4j
    logger.info("Step 3: Saving to Neo4j...")
    count = await create_learning_batch(session, learning_items)

    # Step 4: Fetch the most recent items to return in the response
    saved = await get_all_learnings(session, skip=0, limit=count)
    response_items = [LearningResponse(**item) for item in saved]

    return SyncResponse(
        message=f"Successfully synced {count} learning items.",
        count=count,
        items=response_items
    )
