"""Static page routes with service injection."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service
from jinja2 import Environment, FileSystemLoader
from app.config import get_feature_flags

env = Environment(loader=FileSystemLoader("app/templates"))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_home(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the home page."""
    # Get homepage sections
    result = await content_service.get_homepage_sections()
    
    return HTMLResponse(
        content=env.get_template("index.html").render(
            request=request,
            sections=result.get("sections", {}),
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