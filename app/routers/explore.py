"""
Explore routes for path-based navigation in the digital garden.
"""

import random
from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

from app.services.dependencies import (
    get_content_service,
    get_path_navigation_service,
    get_backlink_service,
    get_growth_stage_renderer
)
from app.services.growth_stage_renderer import GrowthStageRenderer
from app.interfaces import (
    IContentProvider,
    IPathNavigationService,
    IBacklinkService
)

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader("app/templates"))

router = APIRouter()


@router.get("/explore", response_class=HTMLResponse)
async def explore_landing(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer)
):
    """Render the explore landing page."""
    template = env.get_template("explore_landing.html")
    
    # Get recent content for suggestions
    all_content = content_service.get_all_content()
    recent_notes = [c for c in all_content if c.get("content_type") == "notes"][:10]
    
    # Add growth stage symbols
    for note in recent_notes:
        growth_stage = note.get("growth_stage", "seedling")
        note["growth_symbol"] = growth_renderer.render_stage_symbol(growth_stage)
        note["growth_class"] = growth_renderer.get_css_class(growth_stage)
    
    return template.render(
        request=request,
        recent_notes=recent_notes,
        title="Explore the Garden"
    )


@router.get("/wander")
async def wander(
    content_service: IContentProvider = Depends(get_content_service)
):
    """Redirect to a random content page."""
    # Get all available content
    all_content = content_service.get_all_content()
    
    # Filter out drafts and empty content
    valid_content = [
        c for c in all_content 
        if c.get("slug") and c.get("content_type") 
        and c.get("status", "").lower() != "draft"
    ]
    
    if not valid_content:
        # If no content available, redirect to homepage
        return RedirectResponse(url="/", status_code=303)
    
    # Select a random piece of content
    random_content = random.choice(valid_content)
    
    # Build the URL based on content type
    content_type = random_content.get("content_type", "notes")
    slug = random_content.get("slug", "")
    
    # Handle special content types
    if content_type == "bookmarks" and random_content.get("url"):
        # For bookmarks with external URLs, redirect to the bookmark page
        url = f"/bookmarks/{slug}"
    else:
        # For all other content types
        url = f"/{content_type}/{slug}"
    
    return RedirectResponse(url=url, status_code=303)


@router.get("/explore/{path:path}", response_class=HTMLResponse)
async def explore_path(
    path: str,
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
    path_service: IPathNavigationService = Depends(get_path_navigation_service),
    backlink_service: IBacklinkService = Depends(get_backlink_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer)
):
    """Handle exploration path navigation."""
    # Parse the path (comma-separated slugs)
    slugs = [s.strip() for s in path.split(",") if s.strip()]
    
    if not slugs:
        # Redirect to explore landing
        return await explore_landing(request, content_service, growth_renderer)
    
    # Validate the path
    is_valid, error_message = path_service.validate_exploration_path(",".join(slugs))
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Get content for each slug in the path
    path_content = []
    for slug in slugs:
        # Try different content types
        content = None
        for content_type in ["notes", "til", "how_to", "pages"]:
            content = content_service.get_content_by_slug(content_type, slug)
            if content:
                break
        
        if content:
            # Add growth stage rendering
            growth_stage = content.get("growth_stage", "seedling")
            content["growth_symbol"] = growth_renderer.render_stage_symbol(growth_stage)
            content["growth_class"] = growth_renderer.get_css_class(growth_stage)
            
            # Get backlinks
            backlinks = backlink_service.get_backlinks(slug)
            content["backlinks"] = backlinks
            
            path_content.append(content)
    
    # Get the current (last) note
    current_note = path_content[-1] if path_content else None
    
    # Get suggestions for next steps
    suggestions = []
    if current_note:
        # Get forward links from the current note
        forward_links = backlink_service.get_forward_links(current_note.get("slug", ""))
        
        # Filter out notes already in the path
        path_slugs = set(slugs)
        suggestions = [
            link for link in forward_links
            if link.get("slug") not in path_slugs
        ][:5]  # Limit to 5 suggestions
    
    # Determine if this is an HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"
    
    if is_htmx:
        # Return partial template for HTMX updates
        template = env.get_template("partials/explore_path.html")
    else:
        # Return full template
        template = env.get_template("explore.html")
    
    return template.render(
        request=request,
        path_content=path_content,
        current_note=current_note,
        path=path,
        slugs=slugs,
        suggestions=suggestions,
        is_htmx=is_htmx
    )