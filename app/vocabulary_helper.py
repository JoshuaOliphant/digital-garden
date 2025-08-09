# ABOUTME: Helper functions for converting technical terms to garden vocabulary
# ABOUTME: Maps terms like 'created' to 'planted' and provides growth stage styling

def convert_to_garden_vocabulary(term: str) -> str:
    """Convert technical terms to garden vocabulary equivalents."""
    vocabulary_map = {
        "created": "planted",
        "updated": "tended",
    }
    return vocabulary_map.get(term, term)


# Growth stage mappings with emojis and colors
GROWTH_STAGES = {
    "seedling": {
        "emoji": "🌱",
        "color": "#10b981",  # emerald-500
        "description": "New idea, just planted"
    },
    "budding": {
        "emoji": "🌿", 
        "color": "#f59e0b",  # amber-500
        "description": "Growing with some development"
    },
    "growing": {
        "emoji": "🌳",
        "color": "#3b82f6",  # blue-500
        "description": "Actively developing and evolving"
    },
    "evergreen": {
        "emoji": "🌲",
        "color": "#059669",  # emerald-600
        "description": "Mature, stable, and valuable"
    }
}


def get_growth_stage_color(stage: str) -> str:
    """Get the color associated with a growth stage."""
    return GROWTH_STAGES.get(stage, {}).get("color", "#6b7280")  # gray-500 fallback


def get_growth_stage_emoji(stage: str) -> str:
    """Get the emoji associated with a growth stage."""
    return GROWTH_STAGES.get(stage, {}).get("emoji", "🌱")  # seedling fallback