"""
Content routes for the digital garden application.
Handles main content display routes with service injection.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from app.services.dependencies import (
    get_content_service,
    get_backlink_service,
    get_growth_stage_renderer,
)
from app.services.growth_stage_renderer import GrowthStageRenderer
from app.interfaces import IContentProvider, IBacklinkService
# ContentManager is in main.py for now - will be refactored later

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader("app/templates"))

router = APIRouter()


@router.get("/{content_type}/{page_name}", response_class=HTMLResponse)
async def read_content(
    request: Request,
    content_type: str,
    page_name: str,
    content_service: IContentProvider = Depends(get_content_service),
    backlink_service: IBacklinkService = Depends(get_backlink_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer),
):
    """Render a page for ``content_type`` and ``page_name`` as ``HTMLResponse``."""
    try:
        # Use service injection instead of ContentManager
        content_data = content_service.get_content_by_slug(content_type, page_name)
        if not content_data:
            raise HTTPException(status_code=404, detail="Content not found")

        # Get backlinks for this content
        backlinks = backlink_service.get_backlinks(page_name)

        # Get growth stage information
        growth_stage_str = content_data.get("growth_stage", "seedling")
        # Convert string to GrowthStage enum
        from app.models import GrowthStage
        growth_stage = GrowthStage(growth_stage_str.lower())
        growth_symbol = growth_renderer.render_stage_symbol(growth_stage)
        growth_css_class = growth_renderer.render_stage_css_class(growth_stage)

    except Exception as e:
        print(f"Content router error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    # Template rendering logic
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = "partials/content.html" if is_htmx else "individual_content.html"

    # Prepare template context
    context = {
        "request": request,
        "metadata": {
            "title": content_data.get("title", "Content"),
            "created": content_data.get("created"),
            "updated": content_data.get("updated"),
            "tags": content_data.get("tags", []),
            "status": content_data.get("status", ""),
            "growth_stage": content_data.get("growth_stage", "seedling"),
        },
        "content": content_data.get("html", ""),
        "content_type": content_type,
        "growth_symbol": growth_symbol,
        "growth_css_class": growth_css_class,
        "backlinks": backlinks,
        "feature_flags": {"use_compiled_css": True},  # Add feature flags
    }

    return HTMLResponse(
        content=env.get_template(template_name).render(context)
    )
