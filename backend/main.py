"""
GitPuller Backend — FastAPI Application

This is the entry point for the web server. Run with:
    cd backend
    uvicorn main:app --reload

KEY CONCEPT — Application Lifecycle:
  The @app.on_event("startup") hook runs once when the server starts.
  We use it to initialize the database. In production, you'd use
  Alembic migrations instead, but for development this is fine.

KEY CONCEPT — CORS Middleware:
  Browsers block cross-origin requests by default (security feature).
  Since our Next.js frontend (localhost:3000) calls our FastAPI backend
  (localhost:8000), we need to explicitly allow it. The next.config.js
  proxy handles this in production, but CORS is a safety net.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.base import init_database
from src.api.sync import router as sync_router

# Configure logging so we see what's happening in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

# Create the FastAPI application
app = FastAPI(
    title="GitPuller API",
    description="AI-powered learning tracker that analyzes your GitHub commits",
    version="0.1.0",
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


@app.on_event("startup")
def on_startup():
    """Initialize the database when the server starts."""
    init_database()


@app.get("/")
def root():
    """Health check endpoint — useful for monitoring."""
    return {"status": "ok", "app": "GitPuller API"}
