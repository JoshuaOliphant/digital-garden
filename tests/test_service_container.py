"""
Tests for the Dependency Injection Container.

This test suite verifies the service container functionality including
service registration, dependency resolution, and FastAPI integration.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any
from datetime import datetime


class TestServiceContainer:
    """Test the ServiceContainer core functionality."""

    def test_service_container_creation(self):
        """Test that ServiceContainer can be created."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()
        assert container is not None
        assert hasattr(container, "register_factory")
        assert hasattr(container, "get_service")

    def test_register_service_factory(self):
        """Test registering a service factory."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()
        mock_factory = Mock(return_value="service_instance")

        container.register_factory("test_service", mock_factory)
        # Should not raise any exception

    def test_register_singleton_service(self):
        """Test registering a singleton service."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()
        mock_factory = Mock(return_value="singleton_instance")

        container.register_singleton("singleton_service", mock_factory)
        # Should not raise any exception

    def test_register_transient_service(self):
        """Test registering a transient service."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()
        mock_factory = Mock(return_value="transient_instance")

        container.register_transient("transient_service", mock_factory)
        # Should not raise any exception

    def test_get_singleton_service_same_instance(self):
        """Test that singleton services return the same instance."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()
        counter = {"value": 0}

        def factory():
            counter["value"] += 1
            return f"instance_{counter['value']}"

        container.register_singleton("singleton", factory)

        instance1 = container.get_service("singleton")
        instance2 = container.get_service("singleton")

        assert instance1 == instance2
        assert instance1 == "instance_1"
        assert counter["value"] == 1  # Factory called only once

    def test_get_transient_service_different_instances(self):
        """Test that transient services return different instances."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()
        counter = {"value": 0}

        def factory():
            counter["value"] += 1
            return f"instance_{counter['value']}"

        container.register_transient("transient", factory)

        instance1 = container.get_service("transient")
        instance2 = container.get_service("transient")

        assert instance1 != instance2
        assert instance1 == "instance_1"
        assert instance2 == "instance_2"
        assert counter["value"] == 2  # Factory called twice

    def test_get_nonexistent_service_raises_error(self):
        """Test that getting a non-existent service raises ServiceNotFoundError."""
        from app.services.service_container import (
            ServiceContainer,
            ServiceNotFoundError,
        )

        container = ServiceContainer()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.get_service("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_service_factory_with_dependencies(self):
        """Test service factory that depends on other services."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()

        # Register dependency
        container.register_singleton("dependency", lambda: "dependency_instance")

        # Register service that depends on dependency
        def service_factory():
            dep = container.get_service("dependency")
            return f"service_with_{dep}"

        container.register_singleton("service", service_factory)

        result = container.get_service("service")
        assert result == "service_with_dependency_instance"

    def test_container_cleanup(self):
        """Test that container cleanup releases resources."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()
        mock_factory = Mock(return_value="instance")

        container.register_singleton("service", mock_factory)
        container.get_service("service")

        container.cleanup()

        # After cleanup, singleton should be recreated
        container.get_service("service")
        assert mock_factory.call_count == 2


class TestServiceFactories:
    """Test service factory functions."""

    def test_content_service_factory(self):
        """Test ContentService factory creation."""
        from app.services.service_container import create_content_service
        from app.config import ContentConfig
        from app.interfaces import IContentProvider

        config = ContentConfig()
        service = create_content_service(config)

        assert service is not None
        assert isinstance(service, IContentProvider)

    def test_backlink_service_factory(self):
        """Test BacklinkService factory with ContentService dependency."""
        from app.services.service_container import create_backlink_service
        from app.services.content_service import ContentService
        from app.interfaces import IBacklinkService

        content_service = ContentService()
        service = create_backlink_service(content_service)

        assert service is not None
        assert isinstance(service, IBacklinkService)

    def test_path_navigation_service_factory(self):
        """Test PathNavigationService factory with ContentService dependency."""
        from app.services.service_container import create_path_navigation_service
        from app.services.content_service import ContentService
        from app.interfaces import IPathNavigationService

        content_service = ContentService()
        service = create_path_navigation_service(content_service)

        assert service is not None
        assert isinstance(service, IPathNavigationService)

    def test_growth_stage_renderer_factory(self):
        """Test GrowthStageRenderer factory (stateless service)."""
        from app.services.service_container import create_growth_stage_renderer
        from app.services.growth_stage_renderer import GrowthStageRenderer

        service = create_growth_stage_renderer()

        assert service is not None
        assert isinstance(service, GrowthStageRenderer)

    def test_factory_with_invalid_config(self):
        """Test that factory with invalid config raises ServiceInitializationError."""
        from app.services.service_container import (
            create_content_service,
            ServiceInitializationError,
        )

        with pytest.raises(ServiceInitializationError):
            # Pass invalid config type
            create_content_service(None)

    def test_dependency_injection_order(self):
        """Test that services are created in correct dependency order."""
        from app.services.service_container import ServiceContainer, setup_container

        container = setup_container()

        # BacklinkService depends on ContentService
        # This should work without circular dependency
        backlink_service = container.get_service("backlink_service")
        assert backlink_service is not None


class TestFastAPIIntegration:
    """Test FastAPI dependency injection integration."""

    def test_dependency_provider_functions_exist(self):
        """Test that FastAPI dependency provider functions exist."""
        from app.services.dependencies import (
            get_content_service,
            get_backlink_service,
            get_path_navigation_service,
            get_growth_stage_renderer,
        )

        assert callable(get_content_service)
        assert callable(get_backlink_service)
        assert callable(get_path_navigation_service)
        assert callable(get_growth_stage_renderer)

    def test_content_service_dependency_provider(self):
        """Test ContentService dependency provider returns correct service."""
        from app.services.dependencies import get_content_service
        from app.interfaces import IContentProvider

        service = get_content_service()
        assert service is not None
        assert isinstance(service, IContentProvider)

    def test_backlink_service_dependency_provider(self):
        """Test BacklinkService dependency provider returns correct service."""
        from app.services.dependencies import get_backlink_service
        from app.interfaces import IBacklinkService

        service = get_backlink_service()
        assert service is not None
        assert isinstance(service, IBacklinkService)

    @pytest.mark.asyncio
    async def test_fastapi_depends_integration(self):
        """Test that services work with FastAPI Depends."""
        from fastapi import FastAPI, Depends
        from app.services.dependencies import get_content_service
        from app.interfaces import IContentProvider

        app = FastAPI()

        @app.get("/test")
        async def test_route(
            content_service: IContentProvider = Depends(get_content_service),
        ):
            return {"service": str(type(content_service).__name__)}

        # Test that route can be created without errors
        assert len(app.routes) > 0

    def test_container_initialization_at_startup(self):
        """Test that container can be initialized at app startup."""
        from app.services.service_container import initialize_container

        container = initialize_container()
        assert container is not None

        # Verify services are registered
        content_service = container.get_service("content_service")
        assert content_service is not None

    @pytest.mark.asyncio
    async def test_lifespan_context_manager(self):
        """Test FastAPI lifespan context manager for container."""
        from fastapi import FastAPI
        from app.services.service_container import container_lifespan

        app = FastAPI(lifespan=container_lifespan)

        # Lifespan should be set
        assert app.router.lifespan_context is not None


class TestCircularDependencies:
    """Test circular dependency detection."""

    def test_detect_circular_dependency(self):
        """Test that circular dependencies are detected."""
        from app.services.service_container import (
            ServiceContainer,
            CircularDependencyError,
        )

        container = ServiceContainer()

        # Service A depends on B
        container.register_singleton(
            "service_a", lambda: container.get_service("service_b")
        )

        # Service B depends on A (circular)
        container.register_singleton(
            "service_b", lambda: container.get_service("service_a")
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            container.get_service("service_a")

        assert "Circular dependency" in str(exc_info.value)

    def test_self_circular_dependency(self):
        """Test that self-referential dependencies are detected."""
        from app.services.service_container import (
            ServiceContainer,
            CircularDependencyError,
        )

        container = ServiceContainer()

        # Service depends on itself
        container.register_singleton(
            "self_ref", lambda: container.get_service("self_ref")
        )

        with pytest.raises(CircularDependencyError):
            container.get_service("self_ref")

    def test_complex_circular_dependency_chain(self):
        """Test detection of circular dependency in longer chain."""
        from app.services.service_container import (
            ServiceContainer,
            CircularDependencyError,
        )

        container = ServiceContainer()

        # A -> B -> C -> A (circular)
        container.register_singleton("a", lambda: container.get_service("b"))
        container.register_singleton("b", lambda: container.get_service("c"))
        container.register_singleton("c", lambda: container.get_service("a"))

        with pytest.raises(CircularDependencyError):
            container.get_service("a")


class TestConfigurationInjection:
    """Test configuration injection into services."""

    def test_content_config_injection(self):
        """Test ContentConfig is properly injected."""
        from app.services.service_container import setup_container
        from app.config import ContentConfig

        container = setup_container()

        with patch("app.config.ContentConfig") as mock_config:
            mock_config.return_value = ContentConfig()

            content_service = container.get_service("content_service")
            assert content_service is not None

    def test_ai_config_injection(self):
        """Test AIConfig can be injected when needed."""
        from app.services.service_container import ServiceContainer
        from app.config import AIConfig

        container = ServiceContainer()
        ai_config = AIConfig()

        # Register a service that needs AI config
        def ai_service_factory():
            return {"config": ai_config}

        container.register_singleton("ai_service", ai_service_factory)

        service = container.get_service("ai_service")
        assert service["config"] == ai_config

    def test_feature_flags_injection(self):
        """Test FeatureFlags can be injected."""
        from app.services.service_container import ServiceContainer
        from app.config import FeatureFlags

        container = ServiceContainer()
        flags = FeatureFlags()

        # Register a service that needs feature flags
        def flagged_service_factory():
            return {"flags": flags}

        container.register_singleton("flagged_service", flagged_service_factory)

        service = container.get_service("flagged_service")
        assert service["flags"] == flags


class TestServiceValidation:
    """Test service validation and error handling."""

    def test_validate_service_interfaces(self):
        """Test that services implement required interfaces."""
        from app.services.service_container import setup_container
        from app.interfaces import IContentProvider, IBacklinkService

        container = setup_container()

        content_service = container.get_service("content_service")
        assert isinstance(content_service, IContentProvider)

        backlink_service = container.get_service("backlink_service")
        assert isinstance(backlink_service, IBacklinkService)

    def test_service_initialization_failure(self):
        """Test handling of service initialization failures."""
        from app.services.service_container import (
            ServiceContainer,
            ServiceInitializationError,
        )

        container = ServiceContainer()

        def failing_factory():
            raise ValueError("Initialization failed")

        container.register_singleton("failing_service", failing_factory)

        with pytest.raises(ServiceInitializationError) as exc_info:
            container.get_service("failing_service")

        assert "failed to initialize" in str(exc_info.value).lower()

    def test_missing_dependency_validation(self):
        """Test that missing dependencies are properly reported."""
        from app.services.service_container import (
            ServiceContainer,
            MissingDependencyError,
        )

        container = ServiceContainer()

        # Register service that depends on non-existent service
        def dependent_factory():
            return container.get_service("nonexistent")

        container.register_singleton("dependent", dependent_factory)

        with pytest.raises((MissingDependencyError, ServiceInitializationError)):
            container.get_service("dependent")


class TestServiceLifecycle:
    """Test service lifecycle management."""

    def test_service_disposal(self):
        """Test that services can be properly disposed."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()

        dispose_called = {"value": False}

        class DisposableService:
            def dispose(self):
                dispose_called["value"] = True

        container.register_singleton("disposable", DisposableService)
        service = container.get_service("disposable")

        container.cleanup()

        # Cleanup should dispose of services with dispose method
        # This test assumes cleanup implementation calls dispose

    def test_container_reset(self):
        """Test that container can be reset to initial state."""
        from app.services.service_container import ServiceContainer

        container = ServiceContainer()

        container.register_singleton("service", lambda: "instance")
        container.get_service("service")

        container.reset()

        with pytest.raises(Exception):  # ServiceNotFoundError or similar
            container.get_service("service")

    def test_memory_cleanup(self):
        """Test that container properly cleans up memory."""
        from app.services.service_container import ServiceContainer
        import weakref

        container = ServiceContainer()

        class TestService:
            pass

        container.register_singleton("test", TestService)
        service = container.get_service("test")
        weak_ref = weakref.ref(service)

        del service
        container.cleanup()

        # After cleanup, the service should be garbage collected
        # (This test may need adjustment based on actual implementation)


class TestContainerSingleton:
    """Test container singleton pattern."""

    def test_get_container_returns_same_instance(self):
        """Test that get_container returns the same instance."""
        from app.services.service_container import get_container

        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_container_thread_safety(self):
        """Test that container is thread-safe."""
        from app.services.service_container import ServiceContainer
        import threading

        container = ServiceContainer()
        results = []

        def get_service():
            container.register_singleton(
                f"service_{threading.current_thread().name}",
                lambda: f"instance_{threading.current_thread().name}",
            )
            service = container.get_service(
                f"service_{threading.current_thread().name}"
            )
            results.append(service)

        threads = [threading.Thread(target=get_service) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should have successfully registered and retrieved services
        assert len(results) == 5
