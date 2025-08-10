"""
Test suite for logging middleware functionality.
These tests verify request/response logging, correlation IDs, and performance tracking.
"""

import json
import time
from unittest.mock import Mock, patch, AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.logging_middleware import (
    LoggingMiddleware,
    generate_correlation_id,
    should_log_request,
    RequestResponseLog,
)


class TestCorrelationID:
    """Test correlation ID generation and management."""

    def test_generate_correlation_id(self):
        """Test that correlation IDs are valid UUIDs."""
        correlation_id = generate_correlation_id()
        
        # Should be a valid UUID string
        assert isinstance(correlation_id, str)
        assert len(correlation_id) == 36
        
        # Should be parseable as UUID
        uuid = UUID(correlation_id)
        assert str(uuid) == correlation_id

    def test_correlation_id_uniqueness(self):
        """Test that correlation IDs are unique."""
        ids = [generate_correlation_id() for _ in range(100)]
        
        # All should be unique
        assert len(ids) == len(set(ids))


class TestRequestFiltering:
    """Test request filtering logic."""

    def test_should_log_static_assets(self):
        """Test that static assets are filtered out."""
        # Should not log
        assert not should_log_request("/static/css/style.css")
        assert not should_log_request("/static/js/app.js")
        assert not should_log_request("/static/images/logo.png")
        assert not should_log_request("/favicon.ico")
        
        # Should log
        assert should_log_request("/")
        assert should_log_request("/api/content")
        assert should_log_request("/notes/example")

    def test_should_log_health_checks(self):
        """Test health check endpoint filtering."""
        # Should not log health checks (if configured)
        assert not should_log_request("/health")
        assert not should_log_request("/healthz")
        assert not should_log_request("/_health")
        
        # Should log other endpoints
        assert should_log_request("/api/health-data")


class TestLoggingMiddleware:
    """Test the logging middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with logging middleware."""
        app = FastAPI()
        
        # Add logging middleware
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/")
        async def root():
            return {"message": "Hello World"}
        
        @app.get("/error")
        async def error():
            raise ValueError("Test error")
        
        @app.get("/slow")
        async def slow():
            time.sleep(0.1)  # 100ms delay
            return {"message": "Slow response"}
        
        @app.get("/static/test.css")
        async def static():
            return {"message": "Static file"}
        
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_middleware_logs_requests(self, client, caplog):
        """Test that middleware logs incoming requests."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            response = client.get("/")
            
            # Should log request
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            
            # Check log contains expected fields
            assert "request_received" in str(call_args)
            assert "GET" in str(call_args)
            assert "/" in str(call_args)

    def test_middleware_logs_responses(self, client, caplog):
        """Test that middleware logs responses."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            response = client.get("/")
            
            # Should log response
            calls = mock_logger.info.call_args_list
            response_log = next((c for c in calls if "request_completed" in str(c)), None)
            
            assert response_log is not None
            assert "200" in str(response_log)
            assert "duration_ms" in str(response_log)

    def test_middleware_adds_correlation_id(self, client):
        """Test that middleware adds correlation ID to requests."""
        response = client.get("/")
        
        # Should have correlation ID in response headers
        assert "X-Correlation-ID" in response.headers
        correlation_id = response.headers["X-Correlation-ID"]
        
        # Should be valid UUID
        UUID(correlation_id)

    def test_middleware_preserves_existing_correlation_id(self, client):
        """Test that middleware preserves correlation ID from request."""
        correlation_id = generate_correlation_id()
        
        response = client.get("/", headers={"X-Correlation-ID": correlation_id})
        
        # Should preserve the same correlation ID
        assert response.headers["X-Correlation-ID"] == correlation_id

    def test_middleware_logs_errors(self, client):
        """Test that middleware logs errors properly."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            with pytest.raises(ValueError):
                response = client.get("/error")
            
            # Should log error
            mock_logger.error.assert_called()
            error_log = mock_logger.error.call_args
            
            assert "request_failed" in str(error_log)
            assert "ValueError" in str(error_log)

    def test_middleware_tracks_response_time(self, client):
        """Test that middleware tracks response time accurately."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            response = client.get("/slow")
            
            # Find response log
            calls = mock_logger.info.call_args_list
            response_log = next((c for c in calls if "duration_ms" in str(c)), None)
            
            assert response_log is not None
            # Duration should be at least 100ms
            log_data = response_log[1]  # kwargs
            assert log_data.get("duration_ms", 0) >= 100

    def test_middleware_skips_static_assets(self, client):
        """Test that middleware skips logging static assets."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            response = client.get("/static/test.css")
            
            # Should not log static assets
            mock_logger.info.assert_not_called()

    def test_middleware_logs_request_body_size(self, client):
        """Test that middleware logs request body size."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            response = client.post("/", json={"key": "value"})
            
            # Should log body size
            calls = mock_logger.info.call_args_list
            request_log = calls[0] if calls else None
            
            assert request_log is not None
            assert "body_size" in str(request_log)

    def test_middleware_logs_user_agent(self, client):
        """Test that middleware logs user agent."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            response = client.get("/", headers={"User-Agent": "TestClient/1.0"})
            
            # Should log user agent
            calls = mock_logger.info.call_args_list
            request_log = calls[0] if calls else None
            
            assert request_log is not None
            assert "TestClient/1.0" in str(request_log)

    def test_middleware_logs_client_ip(self, client):
        """Test that middleware logs client IP."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            response = client.get("/", headers={"X-Forwarded-For": "192.168.1.1"})
            
            # Should log client IP
            calls = mock_logger.info.call_args_list
            request_log = calls[0] if calls else None
            
            assert request_log is not None
            assert "192.168.1.1" in str(request_log) or "testclient" in str(request_log)


class TestRequestResponseLog:
    """Test the RequestResponseLog model."""

    def test_request_response_log_creation(self):
        """Test creating RequestResponseLog object."""
        log = RequestResponseLog(
            correlation_id="test-123",
            method="GET",
            path="/api/test",
            status_code=200,
            duration_ms=45.6,
            client_ip="127.0.0.1",
            user_agent="TestAgent/1.0",
            body_size=0,
            response_size=256
        )
        
        assert log.correlation_id == "test-123"
        assert log.method == "GET"
        assert log.path == "/api/test"
        assert log.status_code == 200
        assert log.duration_ms == 45.6

    def test_request_response_log_to_dict(self):
        """Test converting RequestResponseLog to dictionary."""
        log = RequestResponseLog(
            correlation_id="test-123",
            method="POST",
            path="/api/data",
            status_code=201,
            duration_ms=120.5
        )
        
        log_dict = log.to_dict()
        
        assert log_dict["correlation_id"] == "test-123"
        assert log_dict["method"] == "POST"
        assert log_dict["path"] == "/api/data"
        assert log_dict["status_code"] == 201
        assert log_dict["duration_ms"] == 120.5
        assert "timestamp" in log_dict

    def test_request_response_log_json_serialization(self):
        """Test JSON serialization of RequestResponseLog."""
        log = RequestResponseLog(
            correlation_id="test-123",
            method="GET",
            path="/api/test",
            status_code=200,
            duration_ms=45.6
        )
        
        json_str = log.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["correlation_id"] == "test-123"
        assert parsed["method"] == "GET"
        assert parsed["status_code"] == 200


class TestMiddlewareIntegration:
    """Test middleware integration with FastAPI app."""

    def test_middleware_with_multiple_endpoints(self):
        """Test middleware works with multiple endpoints."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/api/users")
        async def get_users():
            return []
        
        @app.post("/api/users")
        async def create_user():
            return {"id": 1}
        
        @app.get("/api/posts/{post_id}")
        async def get_post(post_id: int):
            return {"id": post_id}
        
        client = TestClient(app)
        
        with patch("app.middleware.logging_middleware.logger") as mock_logger:
            # Test different endpoints
            client.get("/api/users")
            client.post("/api/users")
            client.get("/api/posts/123")
            
            # Should log all requests
            assert mock_logger.info.call_count >= 6  # 3 requests + 3 responses

    def test_middleware_async_compatibility(self):
        """Test middleware works with async endpoints."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/async")
        async def async_endpoint():
            import asyncio
            await asyncio.sleep(0.01)
            return {"async": True}
        
        client = TestClient(app)
        
        response = client.get("/async")
        assert response.status_code == 200
        assert response.json() == {"async": True}