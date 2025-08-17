"""
FastAPI dependency providers for service injection.

This module provides FastAPI-compatible dependency functions that can be used
with Depends() to inject services into route handlers.
"""

from app.interfaces import IContentProvider, IBacklinkService, IPathNavigationService
from app.services.growth_stage_renderer import GrowthStageRenderer
from app.services.service_container import get_container


def get_content_service() -> IContentProvider:
    """Get ContentService instance for dependency injection.

    Returns:
        ContentService instance

    Example:
        @app.get("/content")
        async def get_content(
            service: IContentProvider = Depends(get_content_service)
        ):
            return await service.get_mixed_content()
    """
    container = get_container()
    return container.get_service("content_service")


def get_backlink_service() -> IBacklinkService:
    """Get BacklinkService instance for dependency injection.

    Returns:
        BacklinkService instance

    Example:
        @app.get("/backlinks/{slug}")
        async def get_backlinks(
            slug: str,
            service: IBacklinkService = Depends(get_backlink_service)
        ):
            return service.get_backlinks(slug)
    """
    container = get_container()
    return container.get_service("backlink_service")


def get_path_navigation_service() -> IPathNavigationService:
    """Get PathNavigationService instance for dependency injection.

    Returns:
        PathNavigationService instance

    Example:
        @app.get("/explore/{path:path}")
        async def explore(
            path: str,
            service: IPathNavigationService = Depends(get_path_navigation_service)
        ):
            return service.validate_exploration_path(path)
    """
    container = get_container()
    return container.get_service("path_navigation_service")


def get_growth_stage_renderer() -> GrowthStageRenderer:
    """Get GrowthStageRenderer instance for dependency injection.

    Returns:
        GrowthStageRenderer instance (new instance each time)

    Example:
        @app.get("/render/{stage}")
        async def render_stage(
            stage: str,
            renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer)
        ):
            return renderer.render_stage_symbol(stage)
    """
    container = get_container()
    return container.get_service("growth_stage_renderer")
