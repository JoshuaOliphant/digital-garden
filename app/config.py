"""
Configuration module for the Digital Garden application.
Centralizes all configuration settings and environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache
from pydantic import BaseSettings, Field

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"

# Content directories
CONTENT_DIR = str(APP_DIR / "content")
TEMPLATE_DIR = str(APP_DIR / "templates")
STATIC_DIR = str(APP_DIR / "static")

# Content types
CONTENT_TYPES = ["notes", "til", "bookmarks", "how_to", "pages"]

# Cache settings
CACHE_TTL = 300  # 5 minutes
CACHE_MAX_SIZE = 128

# Feed settings
SITE_URL = "https://joshuaoliph.com"
SITE_TITLE = "Joshua Oliphant's Digital Garden"
SITE_DESCRIPTION = "A digital garden of ideas, notes, and learnings"

# Pagination settings
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Keys and Tokens
    logfire_token: Optional[str] = Field(default=None, env="LOGFIRE_TOKEN")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    
    # Feature flags
    use_compiled_css: bool = Field(default=True, env="USE_COMPILED_CSS")
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    
    # Content settings
    content_dir: str = Field(default=CONTENT_DIR, env="CONTENT_DIR")
    template_dir: str = Field(default=TEMPLATE_DIR, env="TEMPLATE_DIR")
    static_dir: str = Field(default=STATIC_DIR, env="STATIC_DIR")
    
    # Cache settings
    cache_ttl: int = Field(default=CACHE_TTL, env="CACHE_TTL")
    cache_max_size: int = Field(default=CACHE_MAX_SIZE, env="CACHE_MAX_SIZE")
    
    # Site settings
    site_url: str = Field(default=SITE_URL, env="SITE_URL")
    site_title: str = Field(default=SITE_TITLE, env="SITE_TITLE")
    site_description: str = Field(default=SITE_DESCRIPTION, env="SITE_DESCRIPTION")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def get_feature_flags() -> dict:
    """Get feature flags configuration."""
    settings = get_settings()
    return {
        "use_compiled_css": settings.use_compiled_css,
        "enable_cache": settings.enable_cache,
    }


def configure_logfire() -> bool:
    """Configure Logfire logging if token is available."""
    import logfire
    
    settings = get_settings()
    
    if not settings.logfire_token:
        if settings.environment == "production":
            raise RuntimeError(
                "LOGFIRE_TOKEN environment variable is required in production"
            )
        print(
            "Warning: LOGFIRE_TOKEN not set. Running without logging in development mode."
        )
        return False
    
    try:
        # Basic token format validation
        if len(settings.logfire_token) < 10 or len(settings.logfire_token) > 200:
            print(
                f"Warning: LOGFIRE_TOKEN appears to be invalid (length: {len(settings.logfire_token)}). "
                "Running without logging in development mode."
            )
            return False
        
        # Configure Logfire
        logfire.configure(
            token=settings.logfire_token,
            service_name="digital-garden"
        )
        print("Logfire configured successfully")
        return True
        
    except Exception as e:
        print(f"Warning: Failed to configure Logfire: {e}. Running without logging in development mode.")
        return False


# Export commonly used settings
settings = get_settings()