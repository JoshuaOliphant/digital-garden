"""Garden routes with service injection."""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from app.interfaces import IContentProvider, IPathNavigationService
from app.services.dependencies import get_content_service, get_path_navigation_service
from app.services.growth_stage_renderer import GrowthStageRenderer
from app.services.dependencies import get_growth_stage_renderer
from jinja2 import Environment, FileSystemLoader
from app.config import get_feature_flags
import json

env = Environment(loader=FileSystemLoader("app/templates"))
router = APIRouter()


@router.get("/garden", response_class=HTMLResponse)
async def garden_view(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer),
):
    """Render the garden view page."""
    template_name = (
        "partials/garden.html"
        if request.headers.get("HX-Request") == "true"
        else "garden.html"
    )
    
    # Get all content for garden visualization
    result = content_service.get_all_garden_content()
    
    # Add growth symbols to each content item using the service
    from app.models import GrowthStage
    for item in result["content"]:
        growth_stage_str = item.get("growth_stage", "seedling")
        try:
            growth_stage = GrowthStage(growth_stage_str.lower())
            item["growth_symbol"] = growth_renderer.render_stage_symbol(growth_stage)
            item["growth_css_class"] = growth_renderer.render_stage_css_class(growth_stage)
        except (ValueError, KeyError):
            # Fallback to seedling if invalid stage
            item["growth_symbol"] = growth_renderer.render_stage_symbol(GrowthStage.SEEDLING)
            item["growth_css_class"] = growth_renderer.render_stage_css_class(GrowthStage.SEEDLING)
    
    # Get all tags from content
    all_tags = set()
    for item in result["content"]:
        if item.get("tags"):
            all_tags.update(item["tags"])
    
    # Create garden_data object expected by template
    garden_data = {
        "content": result["content"],
        "by_stage": result["by_stage"],
        "total_count": result["total"],
        "tags": sorted(list(all_tags)),
    }
    
    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            garden_data=garden_data,
            growth_renderer=growth_renderer,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/garden-paths", response_class=HTMLResponse)
async def garden_paths(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the garden paths overview page."""
    template_name = (
        "partials/garden_paths.html"
        if request.headers.get("HX-Request") == "true"
        else "garden_paths.html"
    )
    
    # This would typically get predefined paths from configuration
    # For now, returning a placeholder
    paths = []
    
    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            paths=paths,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/garden-path/{path_name}", response_class=HTMLResponse)
async def garden_path_detail(
    request: Request,
    path_name: str,
    content_service: IContentProvider = Depends(get_content_service),
    path_service: IPathNavigationService = Depends(get_path_navigation_service),
):
    """Render a specific garden path."""
    template_name = (
        "partials/garden_path.html"
        if request.headers.get("HX-Request") == "true"
        else "garden_path.html"
    )
    
    # Get path configuration (this would come from a config file)
    # For now, using placeholder logic
    path_items = []
    
    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            path_name=path_name,
            path_items=path_items,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/api/garden-path/{path_name}/progress")
async def garden_path_progress(
    path_name: str,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Get progress for a garden path."""
    # This would calculate actual progress
    # For now, returning placeholder
    progress = {
        "path_name": path_name,
        "completed": 0,
        "total": 0,
        "percentage": 0
    }
    
    return JSONResponse(content=progress)


@router.get("/api/garden-bed/{topic}/items", response_class=HTMLResponse)
async def garden_bed_items(
    request: Request,
    topic: str,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Get items for a specific garden bed (topic)."""
    # Get content by tag/topic
    result = content_service.get_posts_by_tag(topic)
    
    return HTMLResponse(
        content=env.get_template("partials/garden_bed_items.html").render(
            request=request,
            topic=topic,
            items=result.get("posts", []),
            total=result.get("total", 0),
        )
    )