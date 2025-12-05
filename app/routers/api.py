"""API routes with service injection."""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service
from jinja2 import Environment, FileSystemLoader
from app.config import get_feature_flags
from typing import Optional, List
import logfire

env = Environment(loader=FileSystemLoader("app/templates"))
router = APIRouter(prefix="/api")


@router.get("/content-slugs")
async def get_content_slugs(
    content_type: Optional[str] = Query(None, description="Filter by content type: notes, til, bookmarks"),
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return content slugs for terminal autocomplete."""
    all_content = content_service.get_all_content()

    result = {}
    for item in all_content:
        item_type = item.get("type", "notes")
        if content_type and item_type != content_type:
            continue

        if item_type not in result:
            result[item_type] = []

        result[item_type].append({
            "slug": item.get("slug", ""),
            "title": item.get("title", ""),
        })

    return JSONResponse(content=result)


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


@router.get("/search")
async def search_content(
    q: str = Query(..., min_length=1, description="Search query"),
    content_service: IContentProvider = Depends(get_content_service),
):
    """Search content by title and text."""
    all_content = content_service.get_all_content()
    query_lower = q.lower()

    results = []
    for item in all_content:
        # Search in title
        title = item.get("title", "").lower()
        # Search in markdown content
        markdown = item.get("markdown", "").lower()
        # Search in tags
        tags = [t.lower() for t in item.get("tags", [])]

        if query_lower in title or query_lower in markdown or any(query_lower in tag for tag in tags):
            results.append({
                "slug": item.get("slug", ""),
                "title": item.get("title", ""),
                "content_type": item.get("content_type", "notes"),
                "created": str(item.get("created", "")),
                "tags": item.get("tags", []),
                "excerpt": _get_excerpt(item.get("markdown", ""), query_lower),
            })

    # Sort by relevance (title matches first, then by date)
    def relevance_key(item):
        title_match = 1 if query_lower in item["title"].lower() else 0
        return (-title_match, item["created"])

    results.sort(key=relevance_key, reverse=True)

    return JSONResponse(content={
        "query": q,
        "results": results[:20],  # Limit to 20 results
        "total": len(results),
    })


def _get_excerpt(text: str, query: str, context_chars: int = 100) -> str:
    """Extract an excerpt around the query match."""
    text_lower = text.lower()
    pos = text_lower.find(query)

    if pos == -1:
        # No match in text, return start of text
        return text[:context_chars * 2] + "..." if len(text) > context_chars * 2 else text

    # Get context around the match
    start = max(0, pos - context_chars)
    end = min(len(text), pos + len(query) + context_chars)

    excerpt = text[start:end]

    # Add ellipsis if truncated
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."

    return excerpt


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