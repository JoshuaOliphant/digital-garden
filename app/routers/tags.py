"""Tags routes with service injection."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("app/templates"))
from app.config import get_feature_flags

router = APIRouter()


@router.get("/tags/{tag}", response_class=HTMLResponse)
async def read_tag(
    request: Request,
    tag: str,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return posts filtered by tag as an HTMLResponse."""
    template_name = (
        "partials/tag.html"
        if request.headers.get("HX-Request") == "true"
        else "tag.html"
    )

    # Get posts by tag across all content types
    posts_result = content_service.get_posts_by_tag(tag)
    posts = posts_result.get("posts", [])
    total = posts_result.get("total", 0)

    # Get tag counts for sidebar
    tag_counts = content_service.get_tag_counts()

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            posts=posts,
            tag=tag,
            total=total,
            tag_counts=tag_counts,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/topics", response_class=HTMLResponse)
async def read_topics(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the topics/tags overview page as an HTMLResponse."""
    template_name = (
        "partials/topics.html"
        if request.headers.get("HX-Request") == "true"
        else "topics.html"
    )

    # Get all tag counts
    tag_counts = content_service.get_tag_counts()

    # Sort tags by count (descending) and then alphabetically
    sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tag_counts=sorted_tags,
            total_tags=len(sorted_tags),
            feature_flags=get_feature_flags(),
        )
    )


@router.post("/topics/filter", response_class=HTMLResponse)
async def filter_topics_post(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Handle POST request for filtering topics."""
    # This would typically get filter parameters from form data
    # For now, redirect to GET version
    return await read_topics(request, content_service)


@router.get("/topics/filter", response_class=HTMLResponse)
async def filter_topics_get(
    request: Request,
    content_type: str = None,
    min_count: int = 1,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Handle GET request for filtering topics with query parameters."""
    template_name = (
        "partials/topics_filtered.html"
        if request.headers.get("HX-Request") == "true"
        else "topics.html"
    )

    # Get all tag counts
    tag_counts = content_service.get_tag_counts()

    # Apply filters
    filtered_tags = {
        tag: count for tag, count in tag_counts.items() if count >= min_count
    }

    # If content_type filter is specified, filter further
    if content_type:
        # This would require additional logic in ContentService
        # to get tags by content type
        pass

    # Sort tags by count (descending) and then alphabetically
    sorted_tags = sorted(filtered_tags.items(), key=lambda x: (-x[1], x[0]))

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tag_counts=sorted_tags,
            total_tags=len(sorted_tags),
            content_type=content_type,
            min_count=min_count,
            feature_flags=get_feature_flags(),
        )
    )
