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
    enable_garden_paths: bool = False  # Feature flag for Garden Paths functionality

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
    
    @field_validator("enable_garden_paths", mode="before")
    @classmethod
    def validate_enable_garden_paths(cls, v):
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


# Garden Beds Configuration (from topics implementation)
GARDEN_BEDS = {
    "Technology": {
        "tags": ["python", "javascript", "typescript", "react", "fastapi", "htmx", "alpine", "tailwind", "api", "web", "frontend", "backend", "programming", "code", "development", "software", "tech"],
        "color": "bg-blue-200 text-blue-800",
        "icon": "⚡"
    },
    "Creative": {
        "tags": ["design", "ui", "ux", "creativity", "art", "writing", "storytelling", "visual", "graphics", "photography", "music", "drawing"],
        "color": "bg-garden-sage/20 text-garden-sage-dark", 
        "icon": "🎨"
    },
    "Learning": {
        "tags": ["education", "learning", "study", "course", "tutorial", "book", "knowledge", "skill", "training", "teaching", "academic", "research"],
        "color": "bg-green-200 text-green-800",
        "icon": "📚"
    },
    "Research": {
        "tags": ["science", "data", "analysis", "experiment", "methodology", "statistics", "ai", "ml", "machine-learning", "artificial-intelligence", "nlp"],
        "color": "bg-garden-accent/20 text-garden-accent",
        "icon": "🔬"
    },
    "Process": {
        "tags": ["productivity", "workflow", "process", "methodology", "organization", "planning", "management", "strategy", "efficiency", "automation", "tools"],
        "color": "bg-yellow-200 text-yellow-800",
        "icon": "⚙️"
    },
    "Lifestyle": {
        "tags": ["life", "personal", "health", "wellness", "mindfulness", "habits", "growth", "philosophy", "reflection", "thoughts", "experience"],
        "color": "bg-garden-accent/10 text-garden-accent",
        "icon": "🌱"
    }
}

# Curated Garden Paths Configuration
GARDEN_PATHS = {
    "getting-started": {
        "name": "Getting Started with Digital Gardens",
        "description": "A gentle introduction to digital gardening concepts and philosophy",
        "path": ["digital-garden-philosophy", "evergreen-notes", "learning-in-public"],
        "difficulty": "Beginner",
        "estimated_time": "15 minutes",
        "tags": ["digital-garden", "learning", "philosophy"],
        "status": "Evergreen"
    },
    "web-development": {
        "name": "Modern Web Development Journey",
        "description": "From basics to advanced web development concepts",
        "path": ["html-fundamentals", "css-layouts", "javascript-basics", "react-introduction"],
        "difficulty": "Intermediate", 
        "estimated_time": "45 minutes",
        "tags": ["web", "development", "javascript", "react"],
        "status": "Evergreen"
    },
    "productivity-system": {
        "name": "Building a Personal Productivity System",
        "description": "Learn to create and maintain an effective productivity workflow",
        "path": ["productivity-principles", "note-taking-systems", "task-management"],
        "difficulty": "Beginner",
        "estimated_time": "20 minutes", 
        "tags": ["productivity", "workflow", "organization"],
        "status": "Budding"
    }
}


def get_config() -> Dict:
    """Get the complete configuration including garden beds and paths."""
    return {
        "garden_beds": GARDEN_BEDS,
        "garden_paths": GARDEN_PATHS,
        "feature_flags": get_feature_flags(),
        "ai_config": ai_config,
        "content_config": content_config
    }


def setup_directories():
    """Create necessary directories if they don't exist."""
    for directory in [
        content_config.content_dir,
        content_config.backup_dir,
        content_config.cache_dir,
    ]:
        os.makedirs(directory, exist_ok=True)
