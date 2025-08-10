"""
Configuration module for AI services and other settings.
"""

import os
from typing import Dict, Optional

from pydantic_settings import BaseSettings
from pydantic import field_validator


class FeatureFlags(BaseSettings):
    """Feature flags configuration for controlling application behavior."""

    use_compiled_css: bool = False

    @field_validator("use_compiled_css", mode="before")
    @classmethod
    def validate_use_compiled_css(cls, v):
        """Convert various string representations to boolean."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            # Empty string defaults to False
            if v == "":
                return False
            # Handle common boolean string representations
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class AIConfig(BaseSettings):
    """AI service configuration."""

    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    github_username: str = os.getenv("GITHUB_USERNAME", "")

    # Claude model configuration
    claude_model: str = "claude-3-7-sonnet-latest"  # Latest stable model
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.7

    # Model-specific prompts
    system_prompts: Dict[str, str] = {
        "metadata": "You are a metadata specialist helping to organize technical content.",
        "analysis": "You are a content analyst helping to improve technical writing.",
        "search": "You are a search specialist helping to find relevant content.",
        "recommendations": "You are a recommendation specialist helping to suggest related content.",
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ContentConfig(BaseSettings):
    """Content processing configuration."""

    content_dir: str = "app/content"
    backup_dir: str = "app/content_backup"
    cache_dir: str = "app/cache"
    base_url: str = "https://anoliphantneverforgets.com"

    # Content types and their models
    content_types: Dict[str, str] = {
        "bookmarks": "Bookmark",
        "til": "TIL",
        "notes": "Note",
        "how_to": "Note",
        "pages": "Note",
    }

    # Validation settings
    required_fields: Dict[str, type] = {
        "title": str,
        "created": str,
        "updated": str,
        "tags": list,
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instances
def get_feature_flags() -> FeatureFlags:
    """Get a fresh feature flags instance that reads from current environment."""
    return FeatureFlags()


feature_flags = get_feature_flags()
ai_config = AIConfig()
content_config = ContentConfig()


def validate_config() -> Optional[str]:
    """Validate the configuration and return error message if invalid."""
    if not ai_config.anthropic_api_key:
        return "ANTHROPIC_API_KEY environment variable is not set"
    if not ai_config.github_username:
        return "GITHUB_USERNAME environment variable is not set"
    return None


def setup_directories():
    """Create necessary directories if they don't exist."""
    for directory in [
        content_config.content_dir,
        content_config.backup_dir,
        content_config.cache_dir,
    ]:
        os.makedirs(directory, exist_ok=True)
