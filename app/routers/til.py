"""TIL (Today I Learned) routes with service injection."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("app/templates"))
from app.config import get_feature_flags

router = APIRouter()


@router.get("/til", response_class=HTMLResponse)
async def read_til(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the TIL index page as an HTMLResponse."""
    template_name = (
        "partials/til.html"
        if request.headers.get("HX-Request") == "true"
        else "til.html"
    )
    result = content_service.get_til_posts(page=1)

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tils=result["tils"],
            til_tags=result["til_tags"],
            next_page=result["next_page"],
            recent_how_tos=content_service.get_content("how_to", limit=5)["content"],
            recent_notes=content_service.get_content("notes", limit=5)["content"],
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/til/tag/{tag}", response_class=HTMLResponse)
async def read_til_tag(
    request: Request,
    tag: str,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return TIL posts filtered by tag as an HTMLResponse."""
    template_name = (
        "partials/til.html"
        if request.headers.get("HX-Request") == "true"
        else "til.html"
    )
    tils = content_service.get_til_posts_by_tag(tag)

    # Get all tags for the sidebar
    all_tils = content_service.get_til_posts(page=1)

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tils=tils,
            til_tags=all_tils["til_tags"],
            tag=tag,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/til/page/{page}", response_class=HTMLResponse)
async def read_til_page(
    request: Request,
    page: int,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return paginated TIL posts as an HTMLResponse."""
    result = content_service.get_til_posts(page=page)

    return HTMLResponse(
        content=env.get_template("partials/til_page.html").render(
            request=request, tils=result["tils"], next_page=result["next_page"]
        )
    )


@router.get("/til/{til_name}", response_class=HTMLResponse)
async def read_til_detail(
    request: Request,
    til_name: str,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return a specific TIL post as an HTMLResponse."""
    til_content = content_service.get_content_by_slug("til", til_name)

    if not til_content:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="TIL not found")

    template_name = (
        "partials/til_detail.html"
        if request.headers.get("HX-Request") == "true"
        else "til_detail.html"
    )

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            til=til_content,
            feature_flags=get_feature_flags(),
        )
    )
