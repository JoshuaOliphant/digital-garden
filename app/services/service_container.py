"""
Service Container for Dependency Injection.

This module provides a dependency injection container for managing service
lifecycles, dependencies, and configuration injection in the digital garden.
"""

from typing import Any, Callable, Dict, Optional, Set
from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI

from app.config import CONTENT_DIR
from app.interfaces import IContentProvider, IBacklinkService, IPathNavigationService
from app.services.content_service import ContentService
from app.services.backlink_service import BacklinkService
from app.services.path_navigation_service import PathNavigationService
from app.services.growth_stage_renderer import GrowthStageRenderer


# Exception classes
class ServiceNotFoundError(Exception):
    """Raised when a requested service is not registered."""

    pass


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected."""

    pass


class ServiceInitializationError(Exception):
    """Raised when a service fails to initialize."""

    pass


class MissingDependencyError(Exception):
    """Raised when a required dependency is missing."""

    pass


class ServiceContainer:
    """Dependency injection container for managing service lifecycles."""

    def __init__(self):
        """Initialize the service container."""
        self._factories: Dict[str, Callable] = {}
        self._instances: Dict[str, Any] = {}
        self._lifecycles: Dict[str, str] = {}  # 'singleton' or 'transient'
        self._lock = threading.Lock()
        self._resolution_stack: Set[str] = set()  # For circular dependency detection

    def register_factory(
        self, name: str, factory: Callable, lifecycle: str = "singleton"
    ) -> None:
        """Register a service factory.

        Args:
            name: Service name
            factory: Factory function that creates the service
            lifecycle: 'singleton' or 'transient'
        """
        with self._lock:
            self._factories[name] = factory
            self._lifecycles[name] = lifecycle

    def register_singleton(self, name: str, factory: Callable) -> None:
        """Register a singleton service (same instance returned).

        Args:
            name: Service name
            factory: Factory function that creates the service
        """
        self.register_factory(name, factory, "singleton")

    def register_transient(self, name: str, factory: Callable) -> None:
        """Register a transient service (new instance each time).

        Args:
            name: Service name
            factory: Factory function that creates the service
        """
        self.register_factory(name, factory, "transient")

    def get_service(self, name: str) -> Any:
        """Get a service instance by name.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
            ServiceInitializationError: If service fails to initialize
        """
        # Check for circular dependencies
        if name in self._resolution_stack:
            raise CircularDependencyError(
                f"Circular dependency detected: {name} -> {' -> '.join(self._resolution_stack)} -> {name}"
            )

        # Check if service is registered
        if name not in self._factories:
            raise ServiceNotFoundError(f"Service '{name}' not found in container")

        lifecycle = self._lifecycles.get(name, "singleton")

        # Return existing singleton instance if available
        if lifecycle == "singleton" and name in self._instances:
            return self._instances[name]

        # Create new instance
        self._resolution_stack.add(name)
        try:
            factory = self._factories[name]
            instance = factory()

            # Store singleton instances
            if lifecycle == "singleton":
                with self._lock:
                    self._instances[name] = instance

            return instance

        except ServiceNotFoundError:
            # Re-raise service not found as missing dependency
            raise MissingDependencyError(f"Missing dependency for service '{name}'")
        except Exception as e:
            raise ServiceInitializationError(
                f"Service '{name}' failed to initialize: {str(e)}"
            )
        finally:
            self._resolution_stack.discard(name)

    def cleanup(self) -> None:
        """Clean up all singleton instances."""
        with self._lock:
            # Call dispose on any services that have it
            for instance in self._instances.values():
                if hasattr(instance, "dispose"):
                    instance.dispose()

            self._instances.clear()

    def reset(self) -> None:
        """Reset container to initial state."""
        with self._lock:
            self.cleanup()
            self._factories.clear()
            self._lifecycles.clear()


# Service factory functions
def create_content_service(content_dir: Optional[str] = None, cache_ttl: int = 300) -> IContentProvider:
    """Create ContentService instance with configuration.

    Args:
        content_dir: Path to content directory
        cache_ttl: Cache time-to-live in seconds

    Returns:
        ContentService instance
    """
    if content_dir is None:
        content_dir = CONTENT_DIR

    return ContentService(content_dir=content_dir, cache_ttl=cache_ttl)


def create_backlink_service(content_service: IContentProvider) -> IBacklinkService:
    """Create BacklinkService with ContentService dependency.

    Args:
        content_service: ContentService instance

    Returns:
        BacklinkService instance
    """
    return BacklinkService(content_service)


def create_path_navigation_service(
    content_service: IContentProvider,
) -> IPathNavigationService:
    """Create PathNavigationService with ContentService dependency.

    Args:
        content_service: ContentService instance

    Returns:
        PathNavigationService instance
    """
    return PathNavigationService(content_service)


def create_growth_stage_renderer() -> GrowthStageRenderer:
    """Create GrowthStageRenderer instance (stateless service).

    Returns:
        GrowthStageRenderer instance
    """
    return GrowthStageRenderer()


# Container management
_container_instance: Optional[ServiceContainer] = None
_container_lock = threading.Lock()


def setup_container() -> ServiceContainer:
    """Set up and configure the service container.

    Returns:
        Configured ServiceContainer instance
    """
    container = ServiceContainer()

    # Register ContentService (singleton)
    container.register_singleton(
        "content_service", lambda: create_content_service(CONTENT_DIR, 300)
    )

    # Register BacklinkService (singleton, depends on ContentService)
    container.register_singleton(
        "backlink_service",
        lambda: create_backlink_service(container.get_service("content_service")),
    )

    # Register PathNavigationService (singleton, depends on ContentService)
    container.register_singleton(
        "path_navigation_service",
        lambda: create_path_navigation_service(
            container.get_service("content_service")
        ),
    )

    # Register GrowthStageRenderer (transient, stateless)
    container.register_transient("growth_stage_renderer", create_growth_stage_renderer)

    return container


def initialize_container() -> ServiceContainer:
    """Initialize the global service container.

    Returns:
        Initialized ServiceContainer instance
    """
    global _container_instance

    with _container_lock:
        if _container_instance is None:
            _container_instance = setup_container()

        return _container_instance


def get_container() -> ServiceContainer:
    """Get the global service container instance.

    Returns:
        Global ServiceContainer instance
    """
    if _container_instance is None:
        return initialize_container()

    return _container_instance


@asynccontextmanager
async def container_lifespan(app: FastAPI):
    """FastAPI lifespan context manager for container initialization and cleanup.

    Args:
        app: FastAPI application instance
    """
    # Initialize container at startup
    container = initialize_container()

    # Store container in app state for access in routes
    app.state.container = container

    yield

    # Clean up container at shutdown
    container.cleanup()
