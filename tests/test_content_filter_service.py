"""
Test suite for ContentFilterService.
Tests filtering content by types, tags, and growth stages with intersection logic.
"""

import pytest
from app.services.content_filter_service import ContentFilterService
from app.services.url_state import URLState
from typing import Dict, List, Any


@pytest.fixture
def filter_service():
    """Create ContentFilterService instance."""
    return ContentFilterService()


@pytest.fixture
def sample_content() -> List[Dict[str, Any]]:
    """Create sample content for testing."""
    return [
        {
            "content_type": "notes",
            "tags": ["python", "fastapi"],
            "growth_stage": "evergreen",
            "title": "FastAPI Guide",
            "created": "2024-01-01",
        },
        {
            "content_type": "til",
            "tags": ["python"],
            "growth_stage": "budding",
            "title": "Python Trick",
            "created": "2024-01-02",
        },
        {
            "content_type": "bookmarks",
            "tags": ["web", "design"],
            "growth_stage": "seedling",
            "title": "Design Resource",
            "created": "2024-01-03",
        },
        {
            "content_type": "notes",
            "tags": ["web"],
            "growth_stage": "evergreen",
            "title": "Web Standards",
            "created": "2024-01-04",
        },
    ]


class TestContentFilterService:
    """Test suite for ContentFilterService."""

    def test_filter_returns_all_content_with_no_filters(
        self, filter_service, sample_content
    ):
        """Test that all content is returned when no filters are applied."""
        url_state = URLState()
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 4
        assert filtered == sample_content

    def test_filter_by_single_content_type(self, filter_service, sample_content):
        """Test filtering by a single content type."""
        url_state = URLState(types=["notes"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 2
        assert all(item["content_type"] == "notes" for item in filtered)
        assert filtered[0]["title"] == "FastAPI Guide"
        assert filtered[1]["title"] == "Web Standards"

    def test_filter_by_multiple_content_types(self, filter_service, sample_content):
        """Test filtering by multiple content types (OR logic)."""
        url_state = URLState(types=["notes", "til"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 3
        assert all(item["content_type"] in ["notes", "til"] for item in filtered)

    def test_filter_by_single_tag(self, filter_service, sample_content):
        """Test filtering by a single tag."""
        url_state = URLState(tags=["python"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 2
        assert all("python" in item["tags"] for item in filtered)
        assert filtered[0]["title"] == "FastAPI Guide"
        assert filtered[1]["title"] == "Python Trick"

    def test_filter_by_multiple_tags_requires_all(self, filter_service, sample_content):
        """Test filtering by multiple tags (AND logic - content must have ALL tags)."""
        url_state = URLState(tags=["python", "fastapi"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 1
        assert filtered[0]["title"] == "FastAPI Guide"
        assert all(tag in filtered[0]["tags"] for tag in ["python", "fastapi"])

    def test_filter_by_growth_stage(self, filter_service, sample_content):
        """Test filtering by growth stage."""
        url_state = URLState(growth=["evergreen"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 2
        assert all(item["growth_stage"] == "evergreen" for item in filtered)

    def test_filter_by_multiple_growth_stages(self, filter_service, sample_content):
        """Test filtering by multiple growth stages (OR logic)."""
        url_state = URLState(growth=["evergreen", "budding"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 3
        assert all(
            item["growth_stage"] in ["evergreen", "budding"] for item in filtered
        )

    def test_combined_filters_apply_intersection(self, filter_service, sample_content):
        """Test that combining filters applies AND logic across filter types."""
        url_state = URLState(types=["notes"], tags=["web"], growth=["evergreen"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert len(filtered) == 1
        assert filtered[0]["title"] == "Web Standards"
        assert filtered[0]["content_type"] == "notes"
        assert "web" in filtered[0]["tags"]
        assert filtered[0]["growth_stage"] == "evergreen"

    def test_filter_returns_empty_when_no_matches(self, filter_service, sample_content):
        """Test that empty list is returned when no content matches filters."""
        url_state = URLState(tags=["nonexistent"])
        filtered = filter_service.filter_content(sample_content, url_state)
        assert filtered == []

    def test_filter_handles_empty_content_list(self, filter_service):
        """Test that filtering empty content list returns empty list."""
        url_state = URLState(types=["notes"])
        filtered = filter_service.filter_content([], url_state)
        assert filtered == []
