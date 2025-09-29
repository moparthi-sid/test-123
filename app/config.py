import os
from typing import Any, Dict, Optional

from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Task Management API"
    
    # Database settings
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./taskmanager.db"
    )
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()