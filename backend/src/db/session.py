"""Neo4j async session management via dependency injection.

KEY CONCEPT — Driver vs Session:
  The Neo4j AsyncDriver manages a CONNECTION POOL internally.
  You create it ONCE at startup, and each request gets a lightweight
  session from the pool. Think of it like:
    - Driver  = the pool manager (lives for the entire app lifetime)
    - Session = a single conversation with the database (lives per-request)

  This is different from SQLAlchemy's engine/session pattern:
    SQLAlchemy: engine → SessionLocal() → session per request
    Neo4j:      driver → driver.session() → session per request
  The driver IS the factory.

KEY CONCEPT — Why Global State?
  We store the driver in a module-level variable (_driver) because:
    1. FastAPI's lifespan creates it at startup
    2. The get_db_session() dependency needs to access it per-request
    3. The lifespan shuts it down at exit
  This is a standard pattern for connection pools in async Python.
"""

import logging
from typing import AsyncGenerator
from neo4j import AsyncGraphDatabase, AsyncSession, AsyncDriver

logger = logging.getLogger(__name__)

# Module-level driver reference — initialized by lifespan, used by dependency
_driver: AsyncDriver | None = None


def init_driver(uri: str, username: str, password: str) -> AsyncDriver:
    """
    Create and store the global async Neo4j driver.

    Called once during FastAPI lifespan startup.
    The driver opens a connection pool to the Neo4j server.

    Args:
        uri: Neo4j bolt URI (e.g. "bolt://localhost:7687")
        username: Neo4j username
        password: Neo4j password

    Returns:
        AsyncDriver: The initialized driver instance
    """
    global _driver
    _driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
    logger.info(f"Neo4j driver created for {uri}")
    return _driver


async def close_driver():
    """
    Close the global driver and drain the connection pool.

    Called once during FastAPI lifespan shutdown.
    After this, no more database operations are possible.
    """
    global _driver
    if _driver:
        await _driver.close()
        logger.info("Neo4j driver closed")
        _driver = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a Neo4j async session.

    Usage in endpoints:
        @router.post("/sync")
        async def sync(session: AsyncSession = Depends(get_db_session)):
            result = await session.run("MATCH (n) RETURN n")

    The session is automatically closed when the request finishes
    thanks to the `async with` context manager + FastAPI's dependency
    lifecycle.

    Raises:
        RuntimeError: If called before the driver is initialized
    """
    if not _driver:
        raise RuntimeError(
            "Neo4j driver not initialized. "
            "Check that the lifespan started correctly and NEO4J_* env vars are set."
        )
    async with _driver.session() as session:
        yield session
