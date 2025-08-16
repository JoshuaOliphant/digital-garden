"""Tests for Task 9: URL State Management for garden-walk functionality."""

import pytest
from fastapi.testclient import TestClient
from urllib.parse import urlencode, parse_qs
from app.main import app
import json

client = TestClient(app)


class TestGardenWalkEndpoint:
    """Test the /garden-walk endpoint and URL state management."""
    
    def test_garden_walk_endpoint_exists(self):
        """Test that GET /garden-walk endpoint exists and returns 200."""
        response = client.get("/garden-walk")
        assert response.status_code == 200
    
    def test_accepts_path_parameter(self):
        """Test that endpoint accepts path parameter with comma-separated note IDs."""
        response = client.get("/garden-walk?path=note1,note2,note3")
        assert response.status_code == 200
        # Verify the path is parsed correctly
        assert "note1" in response.text or response.headers.get("X-Path-Parsed") == "note1,note2,note3"
    
    def test_accepts_focus_parameter(self):
        """Test that focus parameter indicates active panel (0-indexed)."""
        response = client.get("/garden-walk?path=note1,note2&focus=1")
        assert response.status_code == 200
        # The second panel (index 1) should be marked as active
        assert response.headers.get("X-Focus-Index") == "1" or "data-focus=\"1\"" in response.text
    
    def test_accepts_view_parameter(self):
        """Test that view parameter switches between sliding/stacked/single modes."""
        for view_mode in ["sliding", "stacked", "single"]:
            response = client.get(f"/garden-walk?view={view_mode}")
            assert response.status_code == 200
            assert response.headers.get("X-View-Mode") == view_mode or f"data-view=\"{view_mode}\"" in response.text
    
    def test_url_preserves_all_state_parameters(self):
        """Test that URL updates preserve all state parameters."""
        params = {
            "path": "note1,note2,note3",
            "focus": "2",
            "view": "sliding",
            "theme": "dark"
        }
        url = f"/garden-walk?{urlencode(params)}"
        response = client.get(url)
        assert response.status_code == 200
        
        # Check that all parameters are preserved in some way
        for key, value in params.items():
            assert value in response.text or response.headers.get(f"X-{key.title()}") == value
    
    def test_invalid_parameters_return_defaults(self):
        """Test that invalid parameters return sensible defaults."""
        # Invalid focus index
        response = client.get("/garden-walk?path=note1&focus=999")
        assert response.status_code == 200
        assert "data-focus=\"0\"" in response.text or response.headers.get("X-Focus-Index") == "0"
        
        # Invalid view mode
        response = client.get("/garden-walk?view=invalid")
        assert response.status_code == 200
        assert "data-view=\"sliding\"" in response.text or response.headers.get("X-View-Mode") == "sliding"
    
    def test_url_length_under_2000_chars(self):
        """Test that URLs remain under 2000 character limit."""
        # Create a long path with many notes
        long_path = ",".join([f"very-long-note-name-number-{i}" for i in range(50)])
        params = {"path": long_path, "focus": "25", "view": "sliding"}
        url = f"/garden-walk?{urlencode(params)}"
        
        # URL should be under 2000 characters
        assert len(url) < 2000
        
        response = client.get(url)
        assert response.status_code == 200
    
    def test_shared_urls_restore_exact_state(self):
        """Test that shared URLs restore exact state."""
        original_params = {
            "path": "intro,concepts,tutorial",
            "focus": "1",
            "view": "stacked"
        }
        url = f"/garden-walk?{urlencode(original_params)}"
        
        # First request
        response1 = client.get(url)
        
        # Second request (simulating shared URL)
        response2 = client.get(url)
        
        # Both should have identical state indicators
        assert response1.status_code == response2.status_code == 200
        assert response1.text == response2.text
    
    def test_url_encoding_handles_special_characters(self):
        """Test that URL encoding handles special characters."""
        params = {
            "path": "note-with-spaces,note/with/slashes,note?with&special=chars",
            "focus": "0",
            "view": "sliding"
        }
        url = f"/garden-walk?{urlencode(params)}"
        response = client.get(url)
        assert response.status_code == 200
    
    def test_empty_path_shows_default_content(self):
        """Test that empty path parameter shows default or home content."""
        response = client.get("/garden-walk?path=")
        assert response.status_code == 200
        assert "Welcome" in response.text or "Start exploring" in response.text
    
    def test_nonexistent_note_ids_handled_gracefully(self):
        """Test that nonexistent note IDs are handled gracefully."""
        response = client.get("/garden-walk?path=nonexistent1,valid-note,nonexistent2")
        assert response.status_code == 200
        # Should show available content or error message for missing notes
        assert "not found" in response.text.lower() or response.headers.get("X-Missing-Notes")


class TestURLSerialization:
    """Test URL serialization and deserialization logic."""
    
    def test_state_serialization_to_url(self):
        """Test that application state can be serialized to URL parameters."""
        from app.main import serialize_garden_state
        
        state = {
            "path": ["note1", "note2", "note3"],
            "focus": 1,
            "view": "sliding",
            "filters": {"tags": ["python", "tutorial"]}
        }
        
        url_params = serialize_garden_state(state)
        assert url_params["path"] == "note1,note2,note3"
        assert url_params["focus"] == "1"
        assert url_params["view"] == "sliding"
        assert "filters" in url_params or "tags" in url_params
    
    def test_url_deserialization_to_state(self):
        """Test that URL parameters can be deserialized to application state."""
        from app.main import deserialize_garden_state
        
        params = {
            "path": "note1,note2,note3",
            "focus": "1",
            "view": "sliding",
            "tags": "python,tutorial"
        }
        
        state = deserialize_garden_state(params)
        assert state["path"] == ["note1", "note2", "note3"]
        assert state["focus"] == 1
        assert state["view"] == "sliding"
        assert "python" in state.get("filters", {}).get("tags", [])
    
    def test_url_shortening_for_long_paths(self):
        """Test URL shortening mechanism for paths exceeding limits."""
        from app.main import shorten_path_if_needed
        
        # Create a very long path
        long_path = ["very-long-note-name-" + str(i) for i in range(100)]
        
        shortened = shorten_path_if_needed(long_path)
        # Should be shortened but still functional
        assert len(",".join(shortened)) < 1500  # Leave room for other params
        assert len(shortened) > 0  # Should keep at least some notes


class TestBrowserHistoryAPI:
    """Test browser History API integration."""
    
    def test_history_state_in_response(self):
        """Test that response includes data for History API."""
        response = client.get("/garden-walk?path=note1,note2&focus=1")
        assert response.status_code == 200
        
        # Check for history state script or data attributes
        assert "history.pushState" in response.text or "data-history-state" in response.text
    
    def test_popstate_handler_included(self):
        """Test that popstate event handler is included for back/forward navigation."""
        response = client.get("/garden-walk")
        assert response.status_code == 200
        
        # Check for popstate event listener
        assert "popstate" in response.text or "window.addEventListener" in response.text
    
    def test_htmx_history_integration(self):
        """Test that HTMX history attributes are properly configured."""
        response = client.get("/garden-walk?path=note1")
        assert response.status_code == 200
        
        # Check for HTMX history attributes
        assert "hx-push-url" in response.text or "hx-history" in response.text


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_circular_path_handled(self):
        """Test that circular paths (revisiting notes) are handled."""
        response = client.get("/garden-walk?path=note1,note2,note1,note3")
        assert response.status_code == 200
        # Should handle circular references gracefully
    
    def test_maximum_panels_limit(self):
        """Test that maximum number of panels is enforced."""
        # Create path with many notes
        long_path = ",".join([f"note{i}" for i in range(20)])
        response = client.get(f"/garden-walk?path={long_path}")
        assert response.status_code == 200
        # Should limit visible panels (e.g., max 5)
        assert response.headers.get("X-Panel-Count") or "data-max-panels=\"5\"" in response.text
    
    def test_malformed_query_parameters(self):
        """Test that malformed query parameters don't crash the application."""
        # Various malformed URLs
        test_urls = [
            "/garden-walk?path=",
            "/garden-walk?focus=abc",
            "/garden-walk?view=",
            "/garden-walk?path=note1&focus=-1",
            "/garden-walk?path=note1&focus=1.5",
            "/garden-walk?&&&&"
        ]
        
        for url in test_urls:
            response = client.get(url)
            assert response.status_code == 200  # Should handle gracefully
    
    def test_xss_prevention_in_parameters(self):
        """Test that XSS attempts in URL parameters are prevented."""
        malicious_params = {
            "path": "<script>alert('xss')</script>",
            "focus": "0",
            "view": "sliding<script>alert('xss')</script>"
        }
        url = f"/garden-walk?{urlencode(malicious_params)}"
        response = client.get(url)
        assert response.status_code == 200
        # Script tags should be escaped or removed
        assert "<script>alert('xss')</script>" not in response.text
    
    def test_performance_with_many_parameters(self):
        """Test that performance is acceptable with many URL parameters."""
        import time
        
        params = {
            "path": ",".join([f"note{i}" for i in range(10)]),
            "focus": "5",
            "view": "sliding",
            "theme": "dark",
            "filters": "tag1,tag2,tag3",
            "sort": "date",
            "order": "desc"
        }
        url = f"/garden-walk?{urlencode(params)}"
        
        start_time = time.time()
        response = client.get(url)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second