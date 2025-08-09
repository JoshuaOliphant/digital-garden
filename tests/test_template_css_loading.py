# ABOUTME: Tests for conditional CSS loading in templates based on feature flags
# ABOUTME: Validates that base.html correctly switches between CDN and compiled CSS

import pytest
import os
from unittest.mock import patch
from pathlib import Path
from fastapi.testclient import TestClient


class TestTemplateCSSLoading:
    """Test suite for template CSS loading with feature flags."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def base_template_path(self, project_root):
        """Get the path to base.html template."""
        return project_root / "app" / "templates" / "base.html"

    @pytest.fixture
    def app_client(self):
        """Create a test client for the FastAPI app."""
        # Import here to avoid circular imports
        from app.main import app

        return TestClient(app)

    def test_base_template_uses_compiled_css_when_flag_enabled(self, app_client):
        """Test that base.html uses output.css when USE_COMPILED_CSS=true."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            # Make a request to trigger template rendering
            response = app_client.get("/")
            assert response.status_code == 200

            html_content = response.text

            # Check that compiled CSS is loaded
            assert (
                "/static/css/output.css" in html_content
            ), "Should load output.css when flag is enabled"

            # Check that CDN is NOT loaded
            assert (
                "cdn.tailwindcss.com" not in html_content
            ), "Should not load CDN when using compiled CSS"
            assert (
                'script src="https://cdn.tailwindcss.com"' not in html_content
            ), "CDN script should be absent"

    def test_base_template_uses_cdn_when_flag_disabled(self, app_client):
        """Test that base.html uses CDN when USE_COMPILED_CSS=false or unset."""
        # Test with flag explicitly set to false
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "false"}):
            response = app_client.get("/")
            assert response.status_code == 200

            html_content = response.text

            # Check that CDN is loaded
            assert (
                "cdn.tailwindcss.com" in html_content
            ), "Should load CDN when flag is disabled"

            # Check that compiled CSS is NOT loaded (or is loaded but CDN takes precedence)
            # Note: We might still load output.css as a fallback, but CDN should be primary
            assert (
                "tailwind.config" in html_content
            ), "Should have Tailwind config for CDN"

    def test_base_template_defaults_to_cdn_when_flag_unset(self, app_client):
        """Test that base.html defaults to CDN when USE_COMPILED_CSS is not set."""
        # Ensure the flag is not set
        with patch.dict(os.environ, {}, clear=True):
            # Remove USE_COMPILED_CSS if it exists
            os.environ.pop("USE_COMPILED_CSS", None)

            response = app_client.get("/")
            assert response.status_code == 200

            html_content = response.text

            # Should default to CDN (current behavior)
            assert (
                "cdn.tailwindcss.com" in html_content
            ), "Should default to CDN when flag is unset"

    def test_css_link_href_contains_output_css_when_enabled(self, app_client):
        """Test that the CSS link href specifically points to output.css when enabled."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/")
            html_content = response.text

            # Check for specific link tag format
            assert (
                "<link" in html_content
                and 'href="/static/css/output.css"' in html_content
            ), "Should have link tag with href to output.css"

    def test_no_tailwind_cdn_script_when_compiled_enabled(self, app_client):
        """Test that Tailwind CDN script tag is completely absent when using compiled CSS."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response = app_client.get("/")
            html_content = response.text

            # Check that CDN script and config are absent
            assert (
                'script src="https://cdn.tailwindcss.com"' not in html_content
            ), "Tailwind CDN script tag should not be present"
            assert (
                "tailwind.config = {" not in html_content
            ), "Tailwind inline config should not be present"

    def test_tailwind_config_preserved_when_using_cdn(self, app_client):
        """Test that Tailwind configuration is preserved when using CDN."""
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "false"}):
            response = app_client.get("/")
            html_content = response.text

            # Check that configuration is present
            assert (
                "tailwind.config" in html_content
            ), "Tailwind config should be present"
            assert (
                "gridTemplateColumns" in html_content
            ), "Grid template config should be preserved"
            assert "typography" in html_content, "Typography config should be preserved"

    def test_all_routes_work_with_compiled_css(self, app_client):
        """Test that all major routes render without errors when using compiled CSS."""
        routes_to_test = [
            "/",
            "/til",
            "/projects",
            "/now",
            "/about",
        ]

        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            for route in routes_to_test:
                response = app_client.get(route)
                # Some routes might not exist, but they shouldn't cause 500 errors
                assert response.status_code in [
                    200,
                    404,
                ], f"Route {route} should not cause server error with compiled CSS"

                if response.status_code == 200:
                    # If the route exists, check that it loads CSS properly
                    assert (
                        "/static/css/output.css" in response.text
                        or "/static/css/" in response.text
                    ), f"Route {route} should load CSS resources"

    def test_feature_flag_toggle_changes_css_loading(self, app_client):
        """Test that toggling the feature flag changes CSS loading behavior."""
        # First request with CDN
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "false"}):
            response_cdn = app_client.get("/")
            assert "cdn.tailwindcss.com" in response_cdn.text

        # Second request with compiled CSS
        with patch.dict(os.environ, {"USE_COMPILED_CSS": "true"}):
            response_compiled = app_client.get("/")
            assert "/static/css/output.css" in response_compiled.text
            assert "cdn.tailwindcss.com" not in response_compiled.text

    def test_static_css_directory_accessible(self, app_client):
        """Test that the static CSS directory is properly served."""
        # Test that we can access the CSS files directly
        response = app_client.get("/static/css/styles.css")
        assert response.status_code == 200, "Should be able to access styles.css"

        # If output.css exists, it should also be accessible
        response = app_client.get("/static/css/output.css")
        # It may not exist yet, but if it does, it should be accessible
        if response.status_code == 200:
            assert (
                len(response.content) > 0
            ), "output.css should have content if it exists"
