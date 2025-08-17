"""
Explore route handler for path-accumulating navigation.
This module defines the /explore endpoint that allows users to navigate
through content by accumulating a path of notes.
"""

from fastapi import Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from typing import Optional
from app.interfaces import IContentProvider, IPathNavigationService
from app.services.dependencies import get_content_service, get_path_navigation_service


async def explore_route(
    request: Request,
    env,  # Jinja2 environment passed from main.py
    get_feature_flags,  # Feature flags function passed from main.py
    path: Optional[str] = Query(
        None, max_length=500, description="Comma-separated content slugs"
    ),
    content_service: IContentProvider = Depends(get_content_service),
    path_navigation_service: IPathNavigationService = Depends(
        get_path_navigation_service
    ),
) -> HTMLResponse:
    """
    Handle exploration of content through path accumulation.

    Args:
        request: FastAPI Request object
        env: Jinja2 environment for template rendering
        get_feature_flags: Function to get feature flags
        path: Comma-separated list of content slugs
        content_service: Content service for fetching content
        path_navigation_service: Path navigation service for validation

    Returns:
        HTMLResponse with rendered exploration view

    Raises:
        HTTPException: For invalid paths or other errors
    """
    # Handle empty path - show exploration landing page
    if not path or not path.strip():
        template = env.get_template("explore_landing.html")
        return HTMLResponse(
            content=template.render(
                request=request,
                path_string="",
                path_slugs=[],
                content_items=[],
                current_content=None,
                validation_result={"success": True, "errors": [], "valid_slugs": []},
                errors=[],
                is_empty_path=True,
                page_title="Explore the Garden",
                feature_flags=get_feature_flags(),
            )
        )

    # Validate path length (500 character limit)
    if len(path) > 500:
        raise HTTPException(
            status_code=400, detail="Path length exceeds 500 characters"
        )

    # Parse path into slugs
    path_slugs = [slug.strip() for slug in path.split(",") if slug.strip()]

    # Check maximum path length (10 notes)
    if len(path_slugs) > 10:
        raise HTTPException(
            status_code=400, detail="Path exceeds maximum length of 10 notes"
        )

    # Validate the exploration path
    validation_result = path_navigation_service.validate_exploration_path(path)

    # Check for circular references
    if len(path_slugs) > 1:
        circular_check = path_navigation_service.check_circular_references(path_slugs)
        if circular_check.has_cycle:
            raise HTTPException(
                status_code=400,
                detail=f"Circular reference detected: {' -> '.join(circular_check.cycle_path)}",
            )

    # Handle validation errors
    if not validation_result.success:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid path: {'; '.join(validation_result.errors)}",
        )

    # Fetch content for valid slugs
    content_items = []
    for slug in validation_result.valid_slugs:
        # Try to fetch from different content types
        content = None
        for content_type in ["notes", "til", "bookmarks"]:
            content = content_service.get_content_by_slug(content_type, slug)
            if content:
                break

        if content:
            content_items.append(content)

    # Get the current content (last item in path)
    current_content = content_items[-1] if content_items else None

    # Determine template based on HTMX request
    if request.headers.get("HX-Request") == "true":
        # Return partial template for HTMX updates
        template = env.get_template("partials/explore_path.html")
    else:
        # Return full page template
        template = env.get_template("explore.html")

    # Prepare validation result for template
    validation_dict = {
        "success": validation_result.success,
        "errors": validation_result.errors,
        "valid_slugs": validation_result.valid_slugs,
    }

    # Render template with context
    return HTMLResponse(
        content=template.render(
            request=request,
            path_string=path,
            path_slugs=path_slugs,
            content_items=content_items,
            current_content=current_content,
            validation_result=validation_dict,
            errors=validation_result.errors,
            is_empty_path=False,
            page_title=f"Exploring: {' → '.join(path_slugs)}"
            if path_slugs
            else "Explore",
            feature_flags=get_feature_flags(),
        )
    )
