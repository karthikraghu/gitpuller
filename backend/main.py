"""
GitPuller Backend — FastAPI Application

This is the entry point for the web server. Run with:
    cd backend
    python -m uvicorn main:app --reload

KEY CONCEPT — Lifespan Context Manager:
  Replaces the deprecated @app.on_event("startup") / @app.on_event("shutdown").
  Everything BEFORE `yield` runs once at startup.
  Everything AFTER `yield` runs once at shutdown.
  The `yield` itself is when the app is alive and serving requests.

  This pattern is better because:
    1. Startup and shutdown code live in ONE function (easy to read)
    2. Resources created at startup are GUARANTEED to be cleaned up
    3. It's an async context manager, so it works with async drivers

KEY CONCEPT — CORS Middleware:
  Browsers block cross-origin requests by default (security feature).
  Since our Next.js frontend (localhost:3000) calls our FastAPI backend
  (localhost:8000), we need to explicitly allow it.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.db.session import init_driver, close_driver
from src.api.sync import router as sync_router

# Configure logging so we see what's happening in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan — creates and destroys the Neo4j connection pool.

    This runs ONCE, not per-request. The driver it creates is shared
    across all requests via the get_db_session() dependency.
    """
    # ── STARTUP ──────────────────────────────────────────────
    logger.info("Starting up — connecting to Neo4j...")
    driver = init_driver(
        settings.NEO4J_URI,
        settings.NEO4J_USERNAME,
        settings.NEO4J_PASSWORD,
    )
    # verify_connectivity() pings the server to fail fast if creds are wrong
    await driver.verify_connectivity()
    logger.info(f"Neo4j connected at {settings.NEO4J_URI}")

    yield  # ← App is alive and serving requests here

    # ── SHUTDOWN ─────────────────────────────────────────────
    logger.info("Shutting down — closing Neo4j connection pool...")
    await close_driver()
    logger.info("Neo4j disconnected. Goodbye!")


# Create the FastAPI application with the lifespan manager
app = FastAPI(
    title="GitPuller API",
    description="AI-powered learning tracker that analyzes your GitHub commits",
    version="0.2.0",
    lifespan=lifespan,
)

# Allow the Next.js dev server to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register our API routers
app.include_router(sync_router)


@app.get("/")
async def root():
    """Health check endpoint — useful for monitoring."""
    return {"status": "ok", "app": "GitPuller API", "db": "neo4j"}
