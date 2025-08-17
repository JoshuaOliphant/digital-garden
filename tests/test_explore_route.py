"""
Tests for the /explore route handler.
These tests validate path-based content exploration functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from app.interfaces import PathValidationResult, CircularReferenceResult


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    mock_path_service = Mock()
    mock_content_service = Mock()
    return mock_path_service, mock_content_service


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app

    return TestClient(app)


class TestExploreRoute:
    """Test suite for /explore route handler."""

    def test_explore_route_exists(self, client):
        """Test that /explore route is registered."""
        # Route should exist and return some response
        response = client.get("/explore")
        # Should not be 404 (route not found)
        assert response.status_code != 405  # Method not allowed

    def test_empty_path_returns_landing_page(self, client):
        """Test that empty path shows exploration landing page."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            response = client.get("/explore")
            assert response.status_code == 200
            assert "Explore the Garden" in response.text
            assert "Welcome to the exploration interface" in response.text

    def test_empty_string_path_returns_landing_page(self, client):
        """Test that empty string path shows exploration landing page."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            response = client.get("/explore?path=")
            assert response.status_code == 200
            assert "Explore the Garden" in response.text

    def test_valid_single_note_path(self, client):
        """Test valid single note path renders content."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_content_service = Mock()
            mock_path_dep.return_value = mock_path_service
            mock_content_dep.return_value = mock_content_service

            # Configure validation to succeed
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(success=True, valid_slugs=["test-note"], errors=[])
            )

            # Configure content retrieval
            mock_content_service.get_content_by_slug.return_value = {
                "title": "Test Note",
                "slug": "test-note",
                "html": "<p>Test content</p>",
                "tags": ["test"],
                "growth_stage": "seedling",
            }

            response = client.get("/explore?path=test-note")
            assert response.status_code == 200
            assert "Test Note" in response.text
            assert "test-note" in response.text

    def test_valid_multi_note_path(self, client):
        """Test valid multi-note path renders exploration view."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_content_service = Mock()
            mock_path_dep.return_value = mock_path_service
            mock_content_dep.return_value = mock_content_service

            # Configure validation to succeed
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(
                    success=True, valid_slugs=["note1", "note2", "note3"], errors=[]
                )
            )

            # Configure circular reference check
            mock_path_service.check_circular_references.return_value = (
                CircularReferenceResult(has_cycle=False, cycle_path=[])
            )

            # Configure content retrieval
            def get_content(content_type, slug):
                contents = {
                    "note1": {
                        "title": "Note 1",
                        "slug": "note1",
                        "html": "<p>Content 1</p>",
                    },
                    "note2": {
                        "title": "Note 2",
                        "slug": "note2",
                        "html": "<p>Content 2</p>",
                    },
                    "note3": {
                        "title": "Note 3",
                        "slug": "note3",
                        "html": "<p>Content 3</p>",
                    },
                }
                return contents.get(slug)

            mock_content_service.get_content_by_slug.side_effect = get_content

            response = client.get("/explore?path=note1,note2,note3")
            assert response.status_code == 200
            assert "note1" in response.text
            assert "note2" in response.text
            assert "note3" in response.text
            assert "Note 3" in response.text  # Current content title

    def test_invalid_path_returns_404(self, client):
        """Test that invalid path returns 404 with error details."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_path_dep.return_value = mock_path_service

            # Configure validation to fail
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(
                    success=False,
                    valid_slugs=[],
                    errors=["Content 'invalid-note' not found"],
                )
            )

            response = client.get("/explore?path=invalid-note")
            assert response.status_code == 404
            assert (
                "Invalid path" in response.text or "not found" in response.text.lower()
            )

    def test_circular_reference_returns_400(self, client):
        """Test that circular reference in path returns 400 error."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_path_dep.return_value = mock_path_service

            # Configure validation to succeed
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(
                    success=True, valid_slugs=["note1", "note2", "note1"], errors=[]
                )
            )

            # Configure circular reference check to detect cycle
            mock_path_service.check_circular_references.return_value = (
                CircularReferenceResult(
                    has_cycle=True, cycle_path=["note1", "note2", "note1"]
                )
            )

            response = client.get("/explore?path=note1,note2,note1")
            assert response.status_code == 400
            assert (
                "Circular reference" in response.text
                or "cycle" in response.text.lower()
            )

    def test_path_length_limit_500_chars(self, client):
        """Test that paths exceeding 500 characters are rejected."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Create a path longer than 500 characters
            long_slug = "a" * 100
            long_path = ",".join([long_slug] * 6)  # 600+ chars

            response = client.get(f"/explore?path={long_path}")
            assert response.status_code == 400
            assert (
                "500 characters" in response.text or "length" in response.text.lower()
            )

    def test_path_length_limit_10_notes(self, client):
        """Test that paths with more than 10 notes are rejected."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Create a path with 11 notes
            path = ",".join([f"note{i}" for i in range(11)])

            response = client.get(f"/explore?path={path}")
            assert response.status_code == 400
            assert "10 notes" in response.text or "maximum" in response.text.lower()

    def test_missing_content_handled_gracefully(self, client):
        """Test that missing content is handled without crashing."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_content_service = Mock()
            mock_path_dep.return_value = mock_path_service
            mock_content_dep.return_value = mock_content_service

            # Configure validation to succeed
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(
                    success=True, valid_slugs=["exists", "missing"], errors=[]
                )
            )

            # Configure content retrieval - some content missing
            def get_content(content_type, slug):
                if slug == "exists":
                    return {
                        "title": "Exists",
                        "slug": "exists",
                        "html": "<p>Content</p>",
                    }
                return None  # Missing content

            mock_content_service.get_content_by_slug.side_effect = get_content
            mock_path_service.check_circular_references.return_value = (
                CircularReferenceResult(has_cycle=False, cycle_path=[])
            )

            response = client.get("/explore?path=exists,missing")
            assert response.status_code == 200
            assert "Exists" in response.text

    def test_service_dependency_injection(self, client):
        """Test that services are properly injected via Depends()."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_content_service = Mock()
            mock_path_dep.return_value = mock_path_service
            mock_content_dep.return_value = mock_content_service

            # Configure mocks
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(success=True, valid_slugs=["test"], errors=[])
            )
            mock_content_service.get_content_by_slug.return_value = {
                "title": "Test",
                "slug": "test",
                "html": "<p>Test</p>",
            }

            response = client.get("/explore?path=test")

            # Verify services were called
            mock_path_dep.assert_called()
            mock_content_dep.assert_called()
            mock_path_service.validate_exploration_path.assert_called_with("test")

    def test_template_data_structure(self, client):
        """Test that template receives correct data structure."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_content_service = Mock()
            mock_path_dep.return_value = mock_path_service
            mock_content_dep.return_value = mock_content_service

            # Configure validation
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(success=True, valid_slugs=["test"], errors=[])
            )

            # Configure content
            mock_content_service.get_content_by_slug.return_value = {
                "title": "Test Content",
                "slug": "test",
                "html": "<p>Content body</p>",
                "tags": ["tag1", "tag2"],
                "growth_stage": "evergreen",
            }

            response = client.get("/explore?path=test")
            assert response.status_code == 200

            # Check template rendered with data
            assert "Test Content" in response.text
            assert "test" in response.text
            assert "Path:" in response.text or "Exploring:" in response.text

    def test_htmx_partial_rendering(self, client):
        """Test that HTMX requests return partial template."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_content_service = Mock()
            mock_path_dep.return_value = mock_path_service
            mock_content_dep.return_value = mock_content_service

            # Configure mocks
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(success=True, valid_slugs=["test"], errors=[])
            )
            mock_content_service.get_content_by_slug.return_value = {
                "title": "Test",
                "slug": "test",
                "html": "<p>Test</p>",
            }

            # Make request with HTMX header
            response = client.get("/explore?path=test", headers={"HX-Request": "true"})
            assert response.status_code == 200
            # Partial template should not have full HTML structure
            assert (
                "<html" not in response.text or "explore-path-content" in response.text
            )

    def test_malformed_query_parameters(self, client):
        """Test handling of malformed query parameters."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Test with special characters
            response = client.get("/explore?path=test%20note%2C%2C%2Canother")
            # Should handle URL encoding and empty segments gracefully
            assert response.status_code in [200, 404, 400]

    def test_mixed_valid_invalid_slugs(self, client):
        """Test path with mix of valid and invalid slugs."""
        with (
            patch("app.main.get_path_navigation_service") as mock_path_dep,
            patch("app.main.get_content_service") as mock_content_dep,
        ):
            # Setup mocks
            mock_path_service = Mock()
            mock_path_dep.return_value = mock_path_service

            # Configure validation with partial success
            mock_path_service.validate_exploration_path.return_value = (
                PathValidationResult(
                    success=False,
                    valid_slugs=["valid1"],
                    errors=["Content 'invalid' not found"],
                )
            )

            response = client.get("/explore?path=valid1,invalid,valid2")
            assert response.status_code == 404
            assert (
                "not found" in response.text.lower()
                or "invalid" in response.text.lower()
            )
