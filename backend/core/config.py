"""Configuration management for the application."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # API Keys
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Database
    DATABASE_PATH: str = "data/app.db"
    
    # GitHub Settings
    MAX_REPOS: int = 50
    MAX_COMMITS_PER_REPO: int = 10
    REQUEST_TIMEOUT: int = 10
    
    # Gemini Settings
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    def validate(self) -> bool:
        """Validate that required settings are present."""
        if not self.GITHUB_TOKEN:
            print("Error: GITHUB_TOKEN not found in .env file")
            return False
        if not self.GEMINI_API_KEY:
            print("Error: GEMINI_API_KEY not found in .env file")
            return False
        return True


# Global settings instance
settings = Settings()
