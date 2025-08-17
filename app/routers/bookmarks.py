"""Bookmarks routes with service injection."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("app/templates"))
from app.config import get_feature_flags

router = APIRouter()


@router.get("/bookmarks", response_class=HTMLResponse)
async def read_bookmarks(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the bookmarks page as an HTMLResponse."""
    template_name = (
        "partials/bookmarks.html"
        if request.headers.get("HX-Request") == "true"
        else "bookmarks.html"
    )

    bookmarks = content_service.get_bookmarks(limit=None)

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            bookmarks=bookmarks,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/stars", response_class=HTMLResponse)
async def read_stars(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render GitHub stars page as an HTMLResponse."""
    template_name = (
        "partials/stars.html"
        if request.headers.get("HX-Request") == "true"
        else "stars.html"
    )

    # Get starred bookmarks (assuming this is in ContentService)
    bookmarks = content_service.get_bookmarks(limit=None)
    starred_bookmarks = [b for b in bookmarks if b.get("starred", False)]

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            bookmarks=starred_bookmarks,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/stars/page/{page}", response_class=HTMLResponse)
async def read_stars_page(
    request: Request,
    page: int,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return paginated GitHub stars as an HTMLResponse."""
    # Implementation depends on how pagination is handled in ContentService
    bookmarks = content_service.get_bookmarks(limit=None)
    starred_bookmarks = [b for b in bookmarks if b.get("starred", False)]

    # Simple pagination (this could be improved in ContentService)
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    page_bookmarks = starred_bookmarks[start:end]

    return HTMLResponse(
        content=env.get_template("partials/stars_page.html").render(
            request=request,
            bookmarks=page_bookmarks,
            page=page,
            has_next=len(starred_bookmarks) > end,
        )
    )
