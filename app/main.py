"""
Learning Progress Tracker - Main Entry Point

This script orchestrates the workflow:
1. Fetches recent commits from GitHub
2. Analyzes them with Gemini AI
3. Stores learning insights in SQLite database
"""

import json
from app.core.config import settings
from app.db.base import init_database
from app.db.session import get_db_connection
from app.crud.crud_learning import create_learning_batch
from app.services.github_service import fetch_recent_commits
from app.services.gemini_service import analyze_commits_with_ai


def main():
    """Main application workflow."""
    print("=" * 60)
    print("GitHub Learning Progress Tracker")
    print("=" * 60)
    
    # Validate configuration
    if not settings.validate():
        return
    
    # Initialize database
    init_database()
    
    # Step 1: Fetch GitHub commits
    print("\nStep 1: Fetching recent commits from GitHub...")
    push_data = fetch_recent_commits()
    
    if not push_data:
        print("\nNo commits found in the last 24 hours.")
        return
    
    # Step 2: Analyze with Gemini AI
    print("\nStep 2: Analyzing commits with Gemini AI...")
    learning_items = analyze_commits_with_ai(push_data)
    
    # Step 3: Display results
    print("\n" + "=" * 60)
    print("LEARNING ANALYSIS")
    print("=" * 60)
    
    if learning_items:
        print(json.dumps(learning_items, indent=2))
    else:
        print("No meaningful learning concepts identified.")
    
    # Step 4: Save to database
    print("\nStep 3: Saving to database...")
    conn = get_db_connection()
    try:
        count = create_learning_batch(conn, learning_items)
        print(f"Saved {count} learning items to database.")
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
