"""
ContentFilterService: Filters content based on URL state parameters.
Implements intersection logic for filtering by content types, tags, and growth stages.
"""

from typing import Dict, List, Any
from app.services.url_state import URLState


class ContentFilterService:
    """Service for filtering content based on URL state."""

    def filter_content(
        self, content: List[Dict[str, Any]], url_state: URLState
    ) -> List[Dict[str, Any]]:
        """
        Filter content based on URL state parameters.

        Args:
            content: List of content items
            url_state: URL state with filter criteria

        Returns:
            Filtered list of content items

        Filtering logic:
        - Within a field: OR logic (e.g., types=["notes", "til"] returns notes OR til)
        - For tags: AND logic (all specified tags must be present)
        - Across fields: AND logic (all criteria must be satisfied)
        """
        if not content:
            return []

        filtered = content

        # Filter by content types (OR logic within types)
        if url_state.types:
            filtered = [
                item for item in filtered if item.get("content_type") in url_state.types
            ]

        # Filter by tags (AND logic - all tags must be present)
        if url_state.tags:
            filtered = [
                item
                for item in filtered
                if all(tag in item.get("tags", []) for tag in url_state.tags)
            ]

        # Filter by growth stages (OR logic within stages)
        if url_state.growth:
            filtered = [
                item
                for item in filtered
                if item.get("growth_stage") in url_state.growth
            ]

        return filtered
