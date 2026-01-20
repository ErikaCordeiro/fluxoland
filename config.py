"""Application configuration.

Centralized configuration management for the FluxoLand application.
"""

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings."""
    
    def __init__(self):
        # Application
        self.app_name: str = "FluxoLand"
        self.app_version: str = "1.0.0"
        self.debug: bool = os.getenv("DEBUG", "true").lower() == "true"
        
        # Server
        self.host: str = os.getenv("HOST", "127.0.0.1")
        self.port: int = int(os.getenv("PORT", "8000"))
        
        # Database
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "sqlite:///./fluxoland.db"
        )
        
        # Security
        self.session_secret_key: str = os.getenv(
            "SESSION_SECRET_KEY",
            "dev-secret-key-change-in-production"
        )
        
        # Bling Integration
        self.bling_client_id: Optional[str] = os.getenv("BLING_CLIENT_ID")
        self.bling_client_secret: Optional[str] = os.getenv("BLING_CLIENT_SECRET")
        self.bling_redirect_uri: Optional[str] = os.getenv("BLING_REDIRECT_URI")
        
        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings object with application configuration.
    """
    return Settings()


# Global settings instance
settings = get_settings()
