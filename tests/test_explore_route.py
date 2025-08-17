"""
Tests for the /explore route handler.
Focused on high-value integration tests without complex mocking.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


class TestExploreRoute:
    """Test suite for /explore route handler - focused on real functionality."""
    
    def test_explore_route_exists(self, client):
        """Test that /explore route is registered and responds."""
        response = client.get("/explore")
        # Route exists and returns a valid response (not 404 or 405)
        assert response.status_code in [200, 400, 500]  # Any valid response
        assert response.status_code != 404  # Route not found
        assert response.status_code != 405  # Method not allowed
    
    def test_empty_path_returns_landing_page(self, client):
        """Test that empty path shows exploration landing page."""
        response = client.get("/explore")
        assert response.status_code == 200
        assert "Explore" in response.text
        # Should contain landing page content
        assert "Welcome" in response.text or "exploration" in response.text.lower()
    
    def test_empty_string_path_returns_landing_page(self, client):
        """Test that empty string path shows exploration landing page."""
        response = client.get("/explore?path=")
        assert response.status_code == 200
        assert "Explore" in response.text
    
    def test_whitespace_path_returns_landing_page(self, client):
        """Test that whitespace-only path shows exploration landing page."""
        response = client.get("/explore?path=   ")
        assert response.status_code == 200
        assert "Explore" in response.text
    
    def test_path_length_limit_500_chars(self, client):
        """Test that paths exceeding 500 characters are rejected."""
        # Create a path longer than 500 characters
        long_slug = "a" * 100
        long_path = ",".join([long_slug] * 6)  # 600+ chars
        
        response = client.get(f"/explore?path={long_path}")
        # FastAPI returns 422 for query parameter validation errors
        assert response.status_code == 422
        # Should contain error message about length
        assert "500" in response.text or "length" in response.text.lower()
    
    def test_path_length_limit_10_notes(self, client):
        """Test that paths with more than 10 notes are rejected."""
        # Create a path with 11 notes
        path = ",".join([f"note{i}" for i in range(11)])
        
        response = client.get(f"/explore?path={path}")
        assert response.status_code == 400
        # Should contain error message about note count
        assert "10" in response.text or "maximum" in response.text.lower()
    
    def test_malformed_query_parameters(self, client):
        """Test handling of malformed query parameters."""
        # Test with special characters and URL encoding
        test_cases = [
            "/explore?path=test%20note",  # URL encoded space
            "/explore?path=,,,",  # Multiple commas
            "/explore?path=note1,,note2",  # Empty segments
        ]
        
        for test_path in test_cases:
            response = client.get(test_path)
            # Should handle gracefully without server errors
            assert response.status_code in [200, 400, 404]
            assert response.status_code != 500  # No server errors
    
    def test_single_note_path_format(self, client):
        """Test single note path returns appropriate response."""
        response = client.get("/explore?path=test-note")
        # Should handle request without server error
        assert response.status_code in [200, 404]  # Valid or not found
        assert response.status_code != 500  # No server errors
    
    def test_multi_note_path_format(self, client):
        """Test multi-note path returns appropriate response."""
        response = client.get("/explore?path=note1,note2,note3")
        # Should handle request without server error  
        assert response.status_code in [200, 400, 404]  # Valid, invalid, or not found
        assert response.status_code != 500  # No server errors
    
    def test_response_contains_html(self, client):
        """Test that responses contain valid HTML."""
        test_paths = [
            "/explore",
            "/explore?path=",
            "/explore?path=test",
        ]
        
        for path in test_paths:
            response = client.get(path)
            if response.status_code == 200:
                # Should contain HTML content
                assert "<" in response.text and ">" in response.text
                # Should not be empty
                assert len(response.text.strip()) > 0
    
    def test_htmx_header_handling(self, client):
        """Test that HTMX requests are handled appropriately."""
        # Request with HTMX header
        response = client.get(
            "/explore?path=test",
            headers={"HX-Request": "true"}
        )
        
        # Should handle HTMX requests without errors
        assert response.status_code in [200, 400, 404]
        assert response.status_code != 500
    
    def test_route_performance(self, client):
        """Test that route responds within reasonable time."""
        import time
        
        start_time = time.time()
        response = client.get("/explore")
        end_time = time.time()
        
        # Should respond within 5 seconds (generous for integration test)
        assert (end_time - start_time) < 5.0
        assert response.status_code in [200, 400, 404, 500]