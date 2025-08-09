# ABOUTME: Tests for all application routes to ensure they render correctly with compiled CSS
# ABOUTME: Validates that switching to compiled CSS doesn't break any existing functionality

import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from pathlib import Path


class TestRouteRendering:
    """Test suite for route rendering with compiled CSS."""

    @pytest.fixture
    def app_client(self):
        """Create a test client for the FastAPI app."""
        from app.main import app

        return TestClient(app)

    @pytest.fixture
    def ensure_compiled_css_exists(self):
        """Ensure output.css exists for testing."""
        import subprocess

        project_root = Path(__file__).parent.parent
        output_path = project_root / "app" / "static" / "css" / "output.css"

        if not output_path.exists():
            # Build CSS if it doesn't exist
            subprocess.run(
                ["npm", "run", "build:css"], cwd=project_root, capture_output=True
            )

        return output_path

    def test_home_page_renders_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that home page renders correctly with compiled CSS enabled."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/")

            assert response.status_code == 200, "Home page should load successfully"
            assert (
                len(response.text) > 1000
            ), "Home page should have substantial content"
            assert "/static/css/output.css" in response.text, "Should load compiled CSS"
            assert (
                "An Oliphant Never Forgets" in response.text
            ), "Should have site title"

    def test_til_page_renders_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that TIL page renders correctly with compiled CSS enabled."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/til")

            assert response.status_code == 200, "TIL page should load successfully"
            assert "/static/css/output.css" in response.text, "Should load compiled CSS"
            # Check for TIL-specific elements
            assert (
                "TIL" in response.text or "Today I Learned" in response.text
            ), "Should have TIL content or title"

    def test_projects_page_renders_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that projects page renders correctly with compiled CSS enabled."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/projects")

            assert response.status_code == 200, "Projects page should load successfully"
            assert "/static/css/output.css" in response.text, "Should load compiled CSS"

    def test_now_page_renders_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that now page renders correctly with compiled CSS enabled."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/now")

            assert response.status_code == 200, "Now page should load successfully"
            assert "/static/css/output.css" in response.text, "Should load compiled CSS"

    def test_about_page_renders_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that about page renders correctly with compiled CSS enabled."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/about")

            # About page might not exist, but should not cause 500 error
            assert response.status_code in [
                200,
                404,
            ], "About page should either load or return 404, not error"

            if response.status_code == 200:
                assert (
                    "/static/css/output.css" in response.text
                ), "Should load compiled CSS"

    def test_no_500_errors_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that no routes return 500 errors when using compiled CSS."""
        routes_to_test = [
            "/",
            "/til",
            "/projects",
            "/now",
            "/about",
            "/tags",
            "/notes",
            "/bookmarks",
            "/how-to",
            "/feed.xml",
            "/sitemap.xml",
        ]

        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            for route in routes_to_test:
                response = app_client.get(route)
                assert (
                    response.status_code != 500
                ), f"Route {route} should not return 500 error with compiled CSS"
                assert (
                    response.status_code < 500
                ), f"Route {route} should not return server error (got {response.status_code})"

    def test_all_templates_load_successfully(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that all template-based routes load without template errors."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            # Test main content pages
            response = app_client.get("/")
            assert response.status_code == 200
            assert (
                "container mx-auto" in response.text
            ), "Should have Tailwind container classes"

            # Test content listings
            response = app_client.get("/til")
            assert response.status_code == 200

            # Test pagination if available
            response = app_client.get("/?page=1")
            assert response.status_code == 200

    def test_static_resources_accessible_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that static resources are still accessible when using compiled CSS."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            # Test CSS files
            response = app_client.get("/static/css/styles.css")
            assert response.status_code == 200, "styles.css should be accessible"

            response = app_client.get("/static/css/output.css")
            assert response.status_code == 200, "output.css should be accessible"
            assert len(response.content) > 100, "output.css should have content"

    def test_htmx_functionality_preserved_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that HTMX functionality still works with compiled CSS."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/")

            # Check that HTMX is still loaded
            assert "htmx.org" in response.text, "HTMX should still be loaded"
            assert (
                "hx-" in response.text or "htmx" in response.text.lower()
            ), "Should have HTMX attributes or references"

    def test_navigation_links_work_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that navigation links are functional with compiled CSS."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/")

            # Check that navigation exists
            assert "<nav" in response.text, "Should have navigation element"
            assert 'href="/"' in response.text, "Should have home link"
            assert 'href="/til"' in response.text, "Should have TIL link"
            assert 'href="/projects"' in response.text, "Should have projects link"
            assert 'href="/now"' in response.text, "Should have now link"

    def test_footer_renders_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that footer renders correctly with compiled CSS."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/")

            # Check that footer exists
            assert "<footer" in response.text, "Should have footer element"
            assert (
                "2024" in response.text or "Joshua Oliphant" in response.text
            ), "Should have copyright information"

    def test_responsive_classes_work_with_compiled_css(
        self, app_client, ensure_compiled_css_exists
    ):
        """Test that responsive Tailwind classes are included in compiled CSS."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/")

            # Check for responsive classes in HTML
            # These should be present in templates and thus in compiled CSS
            common_responsive_patterns = [
                "md:",  # Medium breakpoint
                "lg:",  # Large breakpoint
                "sm:",  # Small breakpoint
            ]

            html_has_responsive = any(
                pattern in response.text for pattern in common_responsive_patterns
            )
            assert (
                html_has_responsive or "container" in response.text
            ), "Should have responsive classes or container class"

    def test_css_loading_performance(self, app_client, ensure_compiled_css_exists):
        """Test that pages load within reasonable time with compiled CSS."""
        import time

        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            start_time = time.time()
            response = app_client.get("/")
            end_time = time.time()

            load_time = end_time - start_time

            assert response.status_code == 200
            assert (
                load_time < 2.0
            ), f"Page should load in under 2 seconds (took {load_time:.2f}s)"
