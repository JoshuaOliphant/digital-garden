"""
Tests for Task 14: Update Content Route Handlers

This test suite drives the migration from ContentManager static methods 
to service injection for all content route handlers.

Test categories:
- Service injection integration
- Route handler parameter signatures
- Template context enhancements with backlinks
- Performance preservation
- HTMX compatibility
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.services.dependencies import get_content_service, get_backlink_service, get_growth_stage_renderer
from app.interfaces import IContentProvider, IBacklinkService
from app.services.growth_stage_renderer import GrowthStageRenderer


class TestMainContentRouteServiceInjection:
    """Test main content route /{content_type}/{page_name} service integration."""
    
    def test_content_route_has_service_dependency_parameters(self):
        """Test that main content route accepts service dependencies."""
        # This test will fail initially because current route doesn't have service params
        from app.main import app
        
        # Get the route handler function
        route_handlers = [route for route in app.routes if hasattr(route, 'path') and route.path == "/{content_type}/{page_name}"]
        assert len(route_handlers) > 0, "Content route should exist"
        
        route_handler = route_handlers[0]
        # Check that the handler function has service dependency parameters
        import inspect
        sig = inspect.signature(route_handler.endpoint)
        params = list(sig.parameters.keys())
        
        # These service parameters should exist after migration
        assert 'content_service' in params, "Route should have content_service parameter"
        assert 'backlink_service' in params, "Route should have backlink_service parameter"
        assert 'growth_renderer' in params, "Route should have growth_renderer parameter"
    
    def test_content_route_uses_dependency_injection(self):
        """Test that route uses FastAPI Depends() for service injection."""
        from app.main import app
        import inspect
        
        route_handlers = [route for route in app.routes if hasattr(route, 'path') and route.path == "/{content_type}/{page_name}"]
        route_handler = route_handlers[0]
        sig = inspect.signature(route_handler.endpoint)
        
        # Check that service parameters use Depends()
        for param_name in ['content_service', 'backlink_service', 'growth_renderer']:
            if param_name in sig.parameters:
                param = sig.parameters[param_name]
                # Should have a default value that's a Depends() call
                assert param.default is not None, f"{param_name} should have Depends() default"

    @pytest.mark.asyncio
    async def test_content_route_calls_content_service_not_content_manager(self):
        """Test that route calls ContentService instead of ContentManager static methods."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_backlink_service = Mock(spec=IBacklinkService)
        mock_growth_renderer = Mock(spec=GrowthStageRenderer)
        
        # Mock service returns
        mock_content_service.get_content_by_slug.return_value = {
            "title": "Test Note",
            "html": "<p>Test content</p>",
            "metadata": {"growth_stage": "seedling", "tags": ["test"]},
            "content_type": "notes"
        }
        mock_backlink_service.get_backlinks.return_value = []
        mock_growth_renderer.render_stage_symbol.return_value = "•"
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        app.dependency_overrides[get_backlink_service] = lambda: mock_backlink_service
        app.dependency_overrides[get_growth_stage_renderer] = lambda: mock_growth_renderer
        
        client = TestClient(app)
        
        # This should call the service, not ContentManager
        response = client.get("/notes/test-note")
        
        # Verify service was called
        mock_content_service.get_content_by_slug.assert_called_with("notes", "test-note")
        
        # Clean up
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_content_route_includes_backlinks_in_template_context(self):
        """Test that route includes backlinks data in template rendering."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_backlink_service = Mock(spec=IBacklinkService)
        
        # Mock content and backlinks
        mock_content_service.get_content_by_slug.return_value = {
            "title": "Test Note",
            "html": "<p>Test content</p>",
            "metadata": {"growth_stage": "seedling"},
            "content_type": "notes"
        }
        mock_backlink_service.get_backlinks.return_value = [
            {
                "source_slug": "related-note",
                "source_title": "Related Note",
                "content_type": "notes",
                "link_context": "This note references the current note"
            }
        ]
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        app.dependency_overrides[get_backlink_service] = lambda: mock_backlink_service
        
        client = TestClient(app)
        response = client.get("/notes/test-note")
        
        # Response should include backlinks information
        assert response.status_code == 200
        assert "Related Note" in response.text, "Template should include backlink titles"
        assert "related-note" in response.text, "Template should include backlink slugs"
        
        # Verify backlink service was called
        mock_backlink_service.get_backlinks.assert_called_with("test-note")
        
        app.dependency_overrides.clear()


class TestMixedContentAPIServiceIntegration:
    """Test /api/mixed-content API service integration."""
    
    def test_mixed_content_api_has_service_dependency(self):
        """Test that mixed content API uses service injection."""
        from app.main import app
        import inspect
        
        # Find the mixed content API route
        api_routes = [route for route in app.routes if hasattr(route, 'path') and route.path == "/api/mixed-content"]
        assert len(api_routes) > 0, "Mixed content API route should exist"
        
        route_handler = api_routes[0]
        sig = inspect.signature(route_handler.endpoint)
        params = list(sig.parameters.keys())
        
        # Should have content service dependency
        assert 'content_service' in params, "API should have content_service parameter"

    @pytest.mark.asyncio
    async def test_mixed_content_api_uses_content_service(self):
        """Test that API calls ContentService.get_mixed_content instead of ContentManager."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_content_service.get_mixed_content.return_value = {
            "content": [
                {"title": "Test", "content_type": "notes", "slug": "test"}
            ],
            "page": 1,
            "total": 1,
            "has_next": False,
            "has_prev": False
        }
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        
        client = TestClient(app)
        response = client.get("/api/mixed-content?page=1&per_page=10")
        
        # Verify service method was called
        mock_content_service.get_mixed_content.assert_called_once()
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        
        app.dependency_overrides.clear()


class TestTILRoutesServiceIntegration:
    """Test TIL routes service integration."""
    
    def test_til_routes_have_service_dependencies(self):
        """Test that TIL routes use service injection."""
        from app.main import app
        import inspect
        
        # Check both TIL routes
        til_listing_routes = [route for route in app.routes if hasattr(route, 'path') and route.path == "/til"]
        til_detail_routes = [route for route in app.routes if hasattr(route, 'path') and route.path == "/til/{til_name}"]
        
        assert len(til_listing_routes) > 0, "TIL listing route should exist"
        assert len(til_detail_routes) > 0, "TIL detail route should exist"
        
        # Check service dependencies
        for route_handler in til_listing_routes + til_detail_routes:
            sig = inspect.signature(route_handler.endpoint)
            params = list(sig.parameters.keys())
            assert 'content_service' in params, f"TIL route {route_handler.path} should have content_service"

    @pytest.mark.asyncio
    async def test_til_detail_route_includes_growth_stage_data(self):
        """Test that TIL detail route includes growth stage information."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_growth_renderer = Mock(spec=GrowthStageRenderer)
        
        mock_content_service.get_content_by_slug.return_value = {
            "title": "Test TIL",
            "html": "<p>Test learning</p>",
            "metadata": {"growth_stage": "budding", "tags": ["learning"]},
            "content_type": "til"
        }
        mock_growth_renderer.render_stage_symbol.return_value = "◐"
        mock_growth_renderer.get_css_class.return_value = "growth-budding"
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        app.dependency_overrides[get_growth_stage_renderer] = lambda: mock_growth_renderer
        
        client = TestClient(app)
        response = client.get("/til/test-til")
        
        # Should include growth stage information
        assert response.status_code == 200
        assert "growth-budding" in response.text or "◐" in response.text, "Should include growth stage indicator"
        
        app.dependency_overrides.clear()


class TestBookmarksRouteServiceIntegration:
    """Test bookmarks route service integration."""
    
    def test_bookmarks_route_has_service_dependency(self):
        """Test that bookmarks route uses service injection."""
        from app.main import app
        import inspect
        
        bookmark_routes = [route for route in app.routes if hasattr(route, 'path') and route.path == "/bookmarks"]
        assert len(bookmark_routes) > 0, "Bookmarks route should exist"
        
        route_handler = bookmark_routes[0]
        sig = inspect.signature(route_handler.endpoint)
        params = list(sig.parameters.keys())
        
        assert 'content_service' in params, "Bookmarks route should have content_service parameter"

    @pytest.mark.asyncio
    async def test_bookmarks_route_uses_content_service(self):
        """Test that bookmarks route calls ContentService instead of ContentManager."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_content_service.get_bookmarks.return_value = [
            {
                "title": "Test Bookmark",
                "url": "https://example.com",
                "metadata": {"tags": ["test"]},
                "content_type": "bookmarks"
            }
        ]
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        
        client = TestClient(app)
        response = client.get("/bookmarks")
        
        # Verify service was called
        mock_content_service.get_bookmarks.assert_called_once()
        assert response.status_code == 200
        
        app.dependency_overrides.clear()


class TestTagRoutesServiceIntegration:
    """Test tag filtering routes service integration."""
    
    def test_tag_route_has_service_dependency(self):
        """Test that tag filtering route uses service injection."""
        from app.main import app
        import inspect
        
        tag_routes = [route for route in app.routes if hasattr(route, 'path') and route.path == "/tags/{tag}"]
        assert len(tag_routes) > 0, "Tag route should exist"
        
        route_handler = tag_routes[0]
        sig = inspect.signature(route_handler.endpoint)
        params = list(sig.parameters.keys())
        
        assert 'content_service' in params, "Tag route should have content_service parameter"

    @pytest.mark.asyncio
    async def test_tag_route_uses_content_service_filtering(self):
        """Test that tag route uses ContentService for filtering."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_content_service.get_content_by_tag.return_value = [
            {
                "title": "Tagged Content",
                "slug": "tagged-content",
                "tags": ["test"],
                "content_type": "notes"
            }
        ]
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        
        client = TestClient(app)
        response = client.get("/tags/test")
        
        # Verify service filtering was called
        mock_content_service.get_content_by_tag.assert_called_with("test")
        assert response.status_code == 200
        
        app.dependency_overrides.clear()


class TestBackwardCompatibilityAndPerformance:
    """Test that migration maintains backward compatibility and performance."""
    
    @pytest.mark.asyncio
    async def test_route_responses_maintain_same_structure(self):
        """Test that route responses maintain the same structure as before."""
        # This is a regression test to ensure API responses don't break
        client = TestClient(app)
        
        # Test various routes maintain expected response structure
        routes_to_test = [
            "/api/mixed-content",
            "/bookmarks",
            "/til"
        ]
        
        for route in routes_to_test:
            response = client.get(route)
            # Should not return 500 errors
            assert response.status_code in [200, 404], f"Route {route} should not have server errors"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_content_route_response_time_under_threshold(self):
        """Test that content routes respond within acceptable time."""
        import time
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/til")  # Test TIL listing route
        end_time = time.time()
        
        response_time = end_time - start_time
        # Should respond within 500ms (generous threshold for testing)
        assert response_time < 0.5, f"Route should respond in <500ms, got {response_time:.3f}s"

    def test_htmx_partial_templates_still_work(self):
        """Test that HTMX partial loading functionality is preserved."""
        client = TestClient(app)
        
        # Test HTMX header handling
        response = client.get("/api/mixed-content", headers={"HX-Request": "true"})
        
        # Should still return JSON for API routes
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")


class TestErrorHandlingWithServices:
    """Test error handling when services fail."""
    
    @pytest.mark.asyncio
    async def test_content_route_handles_service_errors_gracefully(self):
        """Test that routes handle service failures gracefully."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_content_service.get_content_by_slug.side_effect = Exception("Service failure")
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        
        client = TestClient(app)
        response = client.get("/notes/test-note")
        
        # Should handle error gracefully, not return 500
        assert response.status_code in [404, 503], "Should handle service errors gracefully"
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_missing_content_returns_404(self):
        """Test that missing content returns 404 with services."""
        mock_content_service = Mock(spec=IContentProvider)
        mock_content_service.get_content_by_slug.return_value = None
        
        app.dependency_overrides[get_content_service] = lambda: mock_content_service
        
        client = TestClient(app)
        response = client.get("/notes/nonexistent")
        
        assert response.status_code == 404, "Should return 404 for missing content"
        
        app.dependency_overrides.clear()


# Test execution will fail initially because:
# 1. Route handlers don't have service dependency parameters
# 2. Routes still call ContentManager static methods  
# 3. Templates don't include backlinks data
# 4. Service injection is not implemented in routes
#
# These failing tests will guide the implementation in Phase 3.2 (GREEN)