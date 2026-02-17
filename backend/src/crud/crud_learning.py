"""CRUD operations for Learning nodes in Neo4j.

KEY CONCEPT — Cypher vs SQL:
  SQL thinks in tables:   SELECT * FROM learnings WHERE date = '2025-01-01'
  Cypher thinks in graphs: MATCH (l:Learning {date: '2025-01-01'}) RETURN l

  In Cypher:
    - MATCH  = find existing nodes/relationships (like SELECT)
    - CREATE = create new nodes/relationships (like INSERT)
    - RETURN = what to send back (like SELECT columns)
    - UNWIND = iterate over a list (like a loop for batch operations)

KEY CONCEPT — Neo4j IDs:
  Neo4j doesn't have auto-increment integer IDs like SQL.
  Each node gets an internal `elementId()` (a string like "4:abc:123").
  We use this as our node identifier instead of integer IDs.
"""

import logging
from typing import List, Optional, Dict
from neo4j import AsyncSession
from src.schemas.learning import LearningCreate

logger = logging.getLogger(__name__)


async def create_learning(session: AsyncSession, learning: LearningCreate) -> Dict:
    """
    Create a single Learning node in Neo4j.

    Args:
        session: Neo4j async session
        learning: Validated LearningCreate Pydantic object

    Returns:
        Dict with the created node's properties + id
    """
    # CREATE makes a new node with the :Learning label and these properties.
    # datetime() is Neo4j's built-in function for current timestamp.
    query = """
    CREATE (l:Learning {
        date: $date,
        repo: $repo,
        technology: $technology,
        concept: $concept,
        created_at: datetime()
    })
    RETURN elementId(l) AS id, l.date AS date, l.repo AS repo,
           l.technology AS technology, l.concept AS concept,
           l.created_at AS created_at
    """
    result = await session.run(query, **learning.model_dump())
    record = await result.single()
    return dict(record)


async def create_learning_batch(
    session: AsyncSession, learnings: List[LearningCreate]
) -> int:
    """
    Batch-create Learning nodes using Cypher's UNWIND.

    UNWIND takes a list and iterates over it in a single query —
    much faster than running CREATE once per item. Think of it
    like SQL's INSERT INTO ... VALUES (...), (...), (...).

    Args:
        session: Neo4j async session
        learnings: List of validated LearningCreate Pydantic objects

    Returns:
        int: Number of nodes created
    """
    if not learnings:
        return 0

    # UNWIND $items AS item → loops over the list
    # CREATE (l:Learning {...}) → creates one node per iteration
    query = """
    UNWIND $items AS item
    CREATE (l:Learning {
        date: item.date,
        repo: item.repo,
        technology: item.technology,
        concept: item.concept,
        created_at: datetime()
    })
    RETURN count(l) AS count
    """
    items = [l.model_dump() for l in learnings]
    result = await session.run(query, items=items)
    record = await result.single()
    count = record["count"]
    logger.info(f"Created {count} Learning nodes")
    return count


async def get_all_learnings(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Dict]:
    """
    Retrieve all Learning nodes with pagination, newest first.

    ORDER BY l.created_at DESC = newest first (like SQL ORDER BY)
    SKIP $skip = offset for pagination
    LIMIT $limit = max results

    Args:
        session: Neo4j async session
        skip: Number of records to skip
        limit: Maximum number to return

    Returns:
        List of dicts with node properties
    """
    query = """
    MATCH (l:Learning)
    RETURN elementId(l) AS id, l.date AS date, l.repo AS repo,
           l.technology AS technology, l.concept AS concept,
           l.created_at AS created_at
    ORDER BY l.created_at DESC
    SKIP $skip
    LIMIT $limit
    """
    result = await session.run(query, skip=skip, limit=limit)
    records = await result.data()
    return records


async def get_learnings_by_date(session: AsyncSession, date: str) -> List[Dict]:
    """
    Retrieve Learning nodes for a specific date.

    Args:
        session: Neo4j async session
        date: Date string in YYYY-MM-DD format

    Returns:
        List of dicts with node properties
    """
    query = """
    MATCH (l:Learning {date: $date})
    RETURN elementId(l) AS id, l.date AS date, l.repo AS repo,
           l.technology AS technology, l.concept AS concept,
           l.created_at AS created_at
    ORDER BY l.created_at DESC
    """
    result = await session.run(query, date=date)
    return await result.data()


async def get_learnings_by_repo(session: AsyncSession, repo: str) -> List[Dict]:
    """
    Retrieve Learning nodes for a specific repository.

    Args:
        session: Neo4j async session
        repo: Repository name (e.g. "user/repo")

    Returns:
        List of dicts with node properties
    """
    query = """
    MATCH (l:Learning {repo: $repo})
    RETURN elementId(l) AS id, l.date AS date, l.repo AS repo,
           l.technology AS technology, l.concept AS concept,
           l.created_at AS created_at
    ORDER BY l.created_at DESC
    """
    result = await session.run(query, repo=repo)
    return await result.data()


async def delete_learning(session: AsyncSession, learning_id: str) -> bool:
    """
    Delete a Learning node by its elementId.

    DETACH DELETE removes the node AND any relationships connected to it.
    Plain DELETE would fail if the node has relationships.

    Args:
        session: Neo4j async session
        learning_id: Neo4j elementId string

    Returns:
        bool: True if a node was deleted, False if not found
    """
    query = """
    MATCH (l:Learning)
    WHERE elementId(l) = $id
    DETACH DELETE l
    RETURN count(l) AS deleted
    """
    result = await session.run(query, id=learning_id)
    record = await result.single()
    return record["deleted"] > 0
