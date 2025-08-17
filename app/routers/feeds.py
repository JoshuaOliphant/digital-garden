"""
Feed routes for the digital garden application.
Handles RSS feeds, sitemap, and robots.txt.
"""

from fastapi import APIRouter
from fastapi.responses import Response

# Note: These functions will need to be imported from ContentManager
# For now, we'll create placeholder imports that will be updated
# when ContentManager is extracted

router = APIRouter()


@router.get("/feed.xml")
@router.get("/feed")
async def rss_feed():
    """Return the RSS feed as an XML ``Response``."""
    # TODO: Import generate_rss_feed from ContentManager when extracted
    # rss_content = generate_rss_feed()
    # For now, return a placeholder
    rss_content = '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Digital Garden</title></channel></rss>'
    return Response(content=rss_content, media_type="application/xml")


@router.get("/sitemap.xml")
async def sitemap():
    """Serve the XML sitemap as an XML ``Response``."""
    # TODO: Import generate_sitemap from ContentManager when extracted
    # sitemap_content = generate_sitemap()
    # For now, return a placeholder
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    return Response(content=sitemap_content, media_type="application/xml")


@router.get("/robots.txt")
async def robots():
    """Serve robots.txt for search engine indexing."""
    # TODO: Import from ContentManager when extracted
    robots_content = """User-agent: *
Allow: /

Sitemap: https://joshuaoliphant.com/sitemap.xml"""
    return Response(content=robots_content, media_type="text/plain")
