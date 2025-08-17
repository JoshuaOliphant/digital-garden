"""API routes with service injection."""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service
from jinja2 import Environment, FileSystemLoader
from app.config import get_feature_flags
from typing import Optional, List
import logfire

env = Environment(loader=FileSystemLoader("app/templates"))
router = APIRouter(prefix="/api")


@router.post("/topics/filter", response_class=HTMLResponse)
async def filter_topics_api(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """API endpoint for filtering topics."""
    # Get form data
    form_data = await request.form()
    content_type = form_data.get("content_type")
    min_count = int(form_data.get("min_count", 1))
    
    # Get filtered tags
    tag_counts = content_service.get_tag_counts()
    
    # Apply filters
    filtered_tags = {
        tag: count for tag, count in tag_counts.items()
        if count >= min_count
    }
    
    # Sort tags
    sorted_tags = sorted(
        filtered_tags.items(),
        key=lambda x: (-x[1], x[0])
    )
    
    return HTMLResponse(
        content=env.get_template("partials/topics_filtered.html").render(
            request=request,
            tag_counts=sorted_tags,
            total_tags=len(sorted_tags),
            content_type=content_type,
            min_count=min_count,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/mixed-content", response_class=HTMLResponse)
async def get_mixed_content_api(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    content_types: Optional[List[str]] = None,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return paginated mixed content as an HTMLResponse."""
    with logfire.span("mixed_content_api", page=page, per_page=per_page):
        try:
            if page < 1:
                raise HTTPException(
                    status_code=400, detail="Page number must be greater than 0"
                )
            if per_page < 1:
                raise HTTPException(
                    status_code=400, detail="Items per page must be greater than 0"
                )
            if per_page > 100:
                raise HTTPException(
                    status_code=400, detail="Items per page cannot exceed 100"
                )

            with logfire.span("fetching_mixed_content"):
                result = await content_service.get_mixed_content(
                    page=page, per_page=per_page
                )
                logfire.debug(
                    "mixed_content_result",
                    next_page=result.get("has_next"),
                    content_length=len(result["content"]),
                    total=result["total"],
                )

            with logfire.span("rendering_template"):
                template = env.get_template("partials/mixed_content_page.html")
                html_content = template.render(
                    mixed_content=result["content"],
                    next_page=result.get("page") + 1 if result.get("has_next") else None,
                    request=request,
                    feature_flags=get_feature_flags(),
                )
                logfire.debug("template_rendered", html_length=len(html_content))

            return HTMLResponse(content=html_content)

        except ValueError as e:
            logfire.error("value_error", error=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logfire.error("unexpected_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))