"""
Feed routes for the digital garden application.
Handles RSS feeds, sitemap, and robots.txt.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, PlainTextResponse
from typing import Optional

from app.services.dependencies import get_content_service
from app.interfaces import IContentProvider
from app.utils.feed_generator import generate_rss_feed, generate_sitemap

router = APIRouter()


@router.get("/feed.xml")
@router.get("/feed")
async def rss_feed(
    content_service: IContentProvider = Depends(get_content_service),
    growth_stage: Optional[str] = Query(None, description="Filter by growth stage: seedling, budding, growing, evergreen")
):
    """Return the RSS feed as an XML ``Response``.
    
    Optional growth_stage parameter allows filtering by growth stage:
    - seedling: New, developing ideas
    - budding: Ideas taking shape
    - growing: Maturing concepts 
    - evergreen: Polished, stable content
    """
    rss_content = generate_rss_feed(content_service, growth_stage=growth_stage)
    return Response(content=rss_content, media_type="application/xml")


@router.get("/sitemap.xml")
async def sitemap(
    content_service: IContentProvider = Depends(get_content_service)
):
    """Serve the XML sitemap as an XML ``Response``."""
    sitemap_content = generate_sitemap(content_service)
    return Response(content=sitemap_content, media_type="application/xml")


@router.get("/robots.txt")
async def robots():
    """Serve robots.txt for search engine indexing."""
    robots_content = """User-agent: *
Allow: /

Sitemap: https://joshuaoliphant.com/sitemap.xml"""
    return PlainTextResponse(content=robots_content)
