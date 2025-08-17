"""Static page routes with service injection."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service, get_growth_stage_renderer
from app.services.growth_stage_renderer import GrowthStageRenderer
from jinja2 import Environment, FileSystemLoader
from app.config import get_feature_flags

env = Environment(loader=FileSystemLoader("app/templates"))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_home(
    request: Request,
    page: int = 1,
    content_service: IContentProvider = Depends(get_content_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer),
):
    """Render the home page with pagination."""
    # Get paginated mixed content (10 posts per page)
    result = await content_service.get_mixed_content(page=page, per_page=10)
    
    # Add growth symbols to each post using the service
    from app.models import GrowthStage
    for post in result.get("content", []):
        growth_stage_str = post.get("growth_stage", "seedling")
        try:
            growth_stage = GrowthStage(growth_stage_str.lower())
            post["growth_symbol"] = growth_renderer.render_stage_symbol(growth_stage)
            post["growth_css_class"] = growth_renderer.render_stage_css_class(growth_stage)
        except (ValueError, KeyError):
            # Fallback to seedling if invalid stage
            post["growth_symbol"] = growth_renderer.render_stage_symbol(GrowthStage.SEEDLING)
            post["growth_css_class"] = growth_renderer.render_stage_css_class(GrowthStage.SEEDLING)
    
    return HTMLResponse(
        content=env.get_template("index.html").render(
            request=request,
            recent_posts=result.get("content", []),
            pagination=result,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/now", response_class=HTMLResponse)
async def read_now(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the /now page."""
    template_name = (
        "partials/now.html"
        if request.headers.get("HX-Request") == "true"
        else "now.html"
    )
    
    # Get the now page content
    now_content = content_service.get_content_by_slug("pages", "now")
    
    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            content=now_content,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/projects", response_class=HTMLResponse)
async def read_projects(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the projects page."""
    template_name = (
        "partials/projects.html"
        if request.headers.get("HX-Request") == "true"
        else "projects.html"
    )
    
    # Get projects content
    projects_content = content_service.get_content_by_slug("pages", "projects")
    
    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            content=projects_content,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "digital-garden"
        }
    )