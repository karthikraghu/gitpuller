"""Configuration management for the application."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # API Keys
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    
    # Neo4j Connection
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    
    # GitHub Settings
    MAX_REPOS: int = 50
    MAX_COMMITS_PER_REPO: int = 10
    REQUEST_TIMEOUT: int = 10
    
    # LLM Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")  # Override in .env
    
    def validate(self) -> bool:
        """Validate that required settings are present."""
        if not self.GITHUB_TOKEN:
            print("Error: GITHUB_TOKEN not found in .env file")
            return False
        if not self.LLM_API_KEY:
            print("Error: LLM_API_KEY not found in .env file")
            return False
        if not self.NEO4J_PASSWORD:
            print("Error: NEO4J_PASSWORD not found in .env file")
            return False
        return True


# Global settings instance
settings = Settings()
