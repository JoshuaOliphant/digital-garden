from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from bs4 import BeautifulSoup
from contextlib import asynccontextmanager
from app.config import get_feature_flags
import markdown
import os
import re
import yaml
from pathlib import Path
import bleach
import random
import httpx
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, TypeVar, Callable, Awaitable
from functools import wraps
from fastapi.responses import Response
from email.utils import format_datetime
from pydantic import ValidationError
import logfire

from .models import BaseContent, Bookmark, TIL, Note
from .config import get_settings, configure_logfire, CONTENT_DIR, TEMPLATE_DIR, SITE_URL
from .logging_config import setup_logging, get_logger, LogConfig
from .middleware.logging_middleware import LoggingMiddleware
from .services.dependencies import get_content_service, get_path_navigation_service, get_backlink_service, get_growth_stage_renderer
from .interfaces import IContentProvider, IPathNavigationService, IBacklinkService
from .services.growth_stage_renderer import GrowthStageRenderer
from .routers import til, bookmarks, tags, garden, pages, api, content, feeds, explore

# Constants
CONTENT_DIR = "app/content"
TEMPLATE_DIR = "app/templates"
STATIC_DIR = "app/static"

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p",
    "pre",
    "code",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "a",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "span",
    "iframe",
]

ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel", "class"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
    "code": ["class"],
    "span": ["class"],
    "iframe": [
        "src",
        "width",
        "height",
        "frameborder",
        "allow",
        "allowfullscreen",
        "title",
        "referrerpolicy",
    ],
}

GITHUB_USERNAME = "JoshuaOliphant"
T = TypeVar("T")

# Initialize HTTP client first since it's used in lifespan
http_client = httpx.AsyncClient(
    timeout=10.0, headers={"Accept": "application/vnd.github.v3+json"}
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to do here
    yield
    # Shutdown: close the HTTP client
    await http_client.aclose()

# Set up logging
setup_logging(LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=os.getenv("LOG_FORMAT", "json"),
    log_dir=Path(os.getenv("LOG_DIR", "logs"))
))

# Initialize FastAPI
app = FastAPI(lifespan=lifespan)

# Add logging middleware
app.add_middleware(
    LoggingMiddleware,
    skip_paths=["/health", "/metrics", "/static"]
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register routers with service injection
app.include_router(til.router)
app.include_router(bookmarks.router)
app.include_router(tags.router)
app.include_router(garden.router)
app.include_router(pages.router)
app.include_router(api.router)
app.include_router(feeds.router)
app.include_router(explore.router)
app.include_router(content.router)

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Configure Logfire with proper token validation
logfire_token = os.getenv("LOGFIRE_TOKEN")
if not logfire_token:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError(
            "LOGFIRE_TOKEN environment variable is required in production"
        )
    print(
        "Warning: LOGFIRE_TOKEN not set. Running without logging in development mode."
    )
else:
    try:
        # Basic token format validation (assuming it should be a non-empty string of reasonable length)
        if not isinstance(logfire_token, str) or len(logfire_token) < 32:
            raise ValueError("Invalid Logfire token format")

        logfire.configure(
            console=logfire.ConsoleOptions(
                min_log_level=(
                    "info" if os.getenv("ENVIRONMENT") == "production" else "debug"
                )
            ),
            token=logfire_token,
        )

        # Test the configuration
        logfire.info(
            "Logfire configured successfully",
            environment=os.getenv("ENVIRONMENT", "development"),
        )

        # Initialize FastAPI instrumentation only if Logfire is properly configured
        logfire.instrument_fastapi(app)
        logfire.instrument_httpx()
        logfire.instrument_pydantic()
    except Exception as e:
        if os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError(f"Failed to configure Logfire in production: {e}")
        print(
            f"Warning: Failed to configure Logfire: {e}. Running without logging in development mode."
        )

class timed_lru_cache:
    """Decorator that adds time-based expiration to an in-memory LRU cache.

    The cache uses regular Python dictionaries and is **not** thread safe.
    It is intended for single-threaded use such as development servers or
    scripts. Use an external cache if you need multi-process or multi-threaded
    safety.
    """

    def __init__(self, maxsize: int = 128, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Any] = {}
        self.last_refresh: Dict[str, float] = {}

    def __call__(
        self, func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:

        @wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> T:
            key = str((args, sorted(kwargs.items())))

            # Check if cache needs refresh
            now = time.time()
            if (
                key not in self.cache
                or now - self.last_refresh.get(key, 0) > self.ttl_seconds
            ):
                self.cache[key] = await func(*args, **kwargs)
                self.last_refresh[key] = now

                # Implement LRU by removing oldest items if cache is too large
                if len(self.cache) > self.maxsize:
                    # Find the key with the oldest timestamp
                    oldest_key = None
                    oldest_time = float("inf")

                    for k, timestamp in self.last_refresh.items():
                        if timestamp < oldest_time:
                            oldest_time = timestamp
                            oldest_key = k

                    if oldest_key is not None:
                        del self.cache[oldest_key]
                        del self.last_refresh[oldest_key]

            return self.cache[key]

        return wrapped

def generate_rss_feed():
    # Get all content
    notes_result = ContentManager.get_content("notes")
    notes = notes_result["content"] if isinstance(notes_result, dict) else notes_result
    
    how_tos_result = ContentManager.get_content("how_to")
    how_tos = how_tos_result["content"] if isinstance(how_tos_result, dict) else how_tos_result
    
    til_result = ContentManager.get_til_posts(page=1, per_page=9999)
    tils = til_result["tils"]

    # Combine all content
    all_content = []
    all_content.extend([(item, "notes") for item in notes])
    all_content.extend([(item, "how_to") for item in how_tos])
    all_content.extend([(item, "til") for item in tils])

    def get_created_date(x):
        item = x[0]
        if isinstance(item, dict):
            date_val = None
            if "created" in item:
                date_val = item.get("created", "")
            elif "metadata" in item and isinstance(item["metadata"], dict):
                date_val = item["metadata"].get("created", "")
            
            # Convert string dates to datetime for consistent comparison
            if isinstance(date_val, str) and date_val:
                try:
                    return datetime.strptime(date_val, "%Y-%m-%d")
                except ValueError:
                    return datetime.min
            elif isinstance(date_val, datetime):
                return date_val
        return datetime.min

    all_content.sort(key=get_created_date, reverse=True)

    # Generate RSS XML
    rss = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    rss += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'

    rss += '<channel>\n'
    rss += '<title>An Oliphant Never Forgets</title>\n'
    rss += f'<link>{SITE_URL}</link>\n'
    rss += '<description>Latest content from An Oliphant Never Forgets</description>\n'
    rss += '<language>en-us</language>\n'
    rss += '<managingEditor>joshua.oliphant@gmail.com (Joshua Oliphant)</managingEditor>\n'
    rss += '<webMaster>joshua.oliphant@gmail.com (Joshua Oliphant)</webMaster>\n'
    rss += f'<atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />\n'

    for item, content_type in all_content:
        rss += "<item>\n"
        rss += f'<title>{item["title"]}</title>\n'
        rss += f'<link>{SITE_URL}/{content_type}/{item["name"]}</link>\n'
        rss += '<author>joshua.oliphant@gmail.com (Joshua Oliphant)</author>\n'

        # Add description/excerpt if available
        if "excerpt" in item:
            rss += f'<description><![CDATA[{item["excerpt"]}]]></description>\n'

        # Handle different date structures
        created_date = None
        if content_type in ["notes", "how_to"]:
            if "created" in item.get("metadata", {}):
                created_date = item["metadata"]["created"]
        else:  # TiL
            if "created" in item:
                created_date = item["created"]

        if created_date:
            date = datetime.strptime(created_date, "%Y-%m-%d")
            rss += f"<pubDate>{format_datetime(date)}</pubDate>\n"

        # Add categories/tags
        if content_type in ["notes", "how_to"]:
            tags = item.get("metadata", {}).get("tags", [])
        else:  # TiL
            tags = item.get("tags", [])

        for tag in tags:
            rss += f"<category>{tag}</category>\n"

        rss += f'<guid>{SITE_URL}/{content_type}/{item["name"]}</guid>\n'
        rss += '</item>\n'

    rss += "</channel>\n"
    rss += "</rss>"

    return rss

def generate_sitemap() -> str:
    """Generate XML sitemap for the site"""
    # Base URL for the site
    base_url = SITE_URL
    
    # Start XML sitemap
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Add static pages
    static_pages = [
        "",  # Home page
        "/now",
        "/til",
        "/projects",
        "/bookmarks",  # Keep bookmarks, remove stars
    ]

    for page in static_pages:
        sitemap += "  <url>\n"
        sitemap += f"    <loc>{base_url}{page}</loc>\n"
        sitemap += "    <changefreq>weekly</changefreq>\n"
        sitemap += "    <priority>0.8</priority>\n"
        sitemap += "  </url>\n"

    # Add notes
    notes_result = ContentManager.get_content("notes")
    notes = notes_result["content"] if isinstance(notes_result, dict) else notes_result
    for note in notes:
        metadata = note.get("metadata", {})
        # Only include content with appropriate status
        if metadata.get("status") in ["Evergreen", "Budding"]:
            sitemap += "  <url>\n"
            sitemap += f'    <loc>{base_url}/notes/{note["name"]}</loc>\n'
            if metadata.get("updated"):
                sitemap += f'    <lastmod>{metadata["updated"]}</lastmod>\n'
            elif metadata.get("created"):
                sitemap += f'    <lastmod>{metadata["created"]}</lastmod>\n'
            sitemap += "    <changefreq>monthly</changefreq>\n"
            sitemap += "    <priority>0.6</priority>\n"
            sitemap += "  </url>\n"

    # Add how-tos
    how_tos_result = ContentManager.get_content("how_to")
    how_tos = how_tos_result["content"] if isinstance(how_tos_result, dict) else how_tos_result
    for how_to in how_tos:
        metadata = how_to.get("metadata", {})
        # Only include content with appropriate status
        if metadata.get("status") in ["Evergreen", "Budding"]:
            sitemap += "  <url>\n"
            sitemap += f'    <loc>{base_url}/how_to/{how_to["name"]}</loc>\n'
            if metadata.get("updated"):
                sitemap += f'    <lastmod>{metadata["updated"]}</lastmod>\n'
            elif metadata.get("created"):
                sitemap += f'    <lastmod>{metadata["created"]}</lastmod>\n'
            sitemap += "    <changefreq>monthly</changefreq>\n"
            sitemap += "    <priority>0.6</priority>\n"
            sitemap += "  </url>\n"

    # Add TIL posts
    til_result = ContentManager.get_til_posts(page=1, per_page=9999)
    for til in til_result["tils"]:
        # Only include content with appropriate status
        if til.get("status") in ["Evergreen", "Budding"]:
            sitemap += "  <url>\n"
            sitemap += f'    <loc>{base_url}/til/{til["name"]}</loc>\n'
            if til.get("updated"):
                sitemap += f'    <lastmod>{til["updated"]}</lastmod>\n'
            elif til.get("created"):
                sitemap += f'    <lastmod>{til["created"]}</lastmod>\n'
            sitemap += "    <changefreq>monthly</changefreq>\n"
            sitemap += "    <priority>0.6</priority>\n"
            sitemap += "  </url>\n"

    # Add bookmarks
    bookmarks = ContentManager.get_bookmarks()
    for bookmark in bookmarks:
        sitemap += "  <url>\n"
        sitemap += f'    <loc>{base_url}/bookmarks/{bookmark["name"]}</loc>\n'
        if bookmark.get("updated"):
            sitemap += f'    <lastmod>{bookmark["updated"]}</lastmod>\n'
        elif bookmark.get("created"):
            sitemap += f'    <lastmod>{bookmark["created"]}</lastmod>\n'
        sitemap += "    <changefreq>monthly</changefreq>\n"
        sitemap += "    <priority>0.4</priority>\n"  # Lower priority for bookmarks
        sitemap += "  </url>\n"

    # Close sitemap
    sitemap += "</urlset>"
    return sitemap

async def rss_feed():
    """Return the RSS feed as an XML ``Response``."""
    rss_content = generate_rss_feed()
    return Response(content=rss_content, media_type="application/xml")

async def sitemap():
    """Serve the XML sitemap as an XML ``Response``."""
    sitemap_content = generate_sitemap()
    return Response(content=sitemap_content, media_type="application/xml")

async def robots():
    """Return ``robots.txt`` as a plain text ``Response``."""
    return Response(
        content=f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml""",
        media_type="text/plain"
    )

# Route handlers
async def read_home(request: Request):
    """Render the home page with Maggie Appleton-inspired garden design."""
    template = env.get_template("garden.html")
    
    # Get all content for filterable garden
    try:
        garden_data = ContentManager.get_all_garden_content()
        print(f"DEBUG: garden_data returned, type: {type(garden_data)}")
        print(f"DEBUG: content count: {len(garden_data.get('content', []))}")
        print(f"DEBUG: tags: {garden_data.get('tags', [])[:5]}...")  # First 5 tags
        
        # Ensure garden_data has all required keys
        if not garden_data or not isinstance(garden_data, dict):
            garden_data = {}
        
        # Ensure all required keys exist with defaults
        garden_data.setdefault("content", [])
        garden_data.setdefault("tags", [])
        garden_data.setdefault("growth_stages", [])
        garden_data.setdefault("content_types", [])
        garden_data.setdefault("total_count", 0)
        
        print(f"DEBUG: Final content count: {len(garden_data['content'])}")
        
    except Exception as e:
        print(f"ERROR getting garden content: {e}")
        import traceback
        traceback.print_exc()
        garden_data = {
            "content": [],
            "tags": [],
            "growth_stages": [],
            "content_types": [],
            "total_count": 0
        }
    
    return HTMLResponse(
        content=template.render(
            request=request,
            garden_data=garden_data,
            feature_flags=get_feature_flags(),
        )
    )

async def read_garden(request: Request):
    """Render the enhanced garden homepage with Maggie Appleton-inspired design."""
    template = env.get_template("garden.html")
    
    # Get all content for filterable garden
    garden_data = ContentManager.get_all_garden_content()
    
    # Ensure garden_data has required keys
    if not garden_data:
        garden_data = {
            "content": [],
            "tags": [],
            "growth_stages": [],
            "content_types": [],
            "total_count": 0
        }
    
    return HTMLResponse(
        content=template.render(
            request=request,
            garden_data=garden_data,
            feature_flags=get_feature_flags(),
        )
    )

async def explore(
    request: Request,
    path: Optional[str] = Query(None, max_length=500, description="Comma-separated content slugs"),
    content_service: IContentProvider = Depends(get_content_service),
    path_navigation_service: IPathNavigationService = Depends(get_path_navigation_service),
) -> HTMLResponse:
    """
    Handle exploration of content through path accumulation.
    """
    from .explore_route import explore_route
    return await explore_route(
        request=request,
        env=env,
        get_feature_flags=get_feature_flags,
        path=path,
        content_service=content_service,
        path_navigation_service=path_navigation_service
    )

async def read_now(request: Request):
    """Display the now page and return an ``HTMLResponse``."""
    template = env.get_template("content_page.html")
    now_content = ContentManager.render_markdown(f"{CONTENT_DIR}/pages/now.md")
    return HTMLResponse(
        content=template.render(
            request=request,
            content=now_content["html"],
            metadata=now_content["metadata"],
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5),
            feature_flags=get_feature_flags(),
        )
    )

async def read_tag(request: Request, tag: str):
    """Return posts tagged with ``tag`` as an ``HTMLResponse``."""
    # Get content type from query parameter, default to all
    content_type = request.query_params.get("type")
    content_types = [content_type] if content_type else None

    posts = ContentManager.get_posts_by_tag(tag, content_types=content_types)
    template_name = (
        "partials/tags.html"
        if request.headers.get("HX-Request") == "true"
        else "tags.html"
    )

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tag=tag,
            posts=posts,
            content_type=content_type,
            feature_flags=get_feature_flags(),
        )
    )

async def topics_page(request: Request):
    """Display topics organized by garden beds."""
    topics_data = ContentManager.get_topics_data()
    
    # Calculate totals
    total_tags = sum(len(bed["tags"]) for bed in topics_data.values())
    total_content = sum(bed["total_count"] for bed in topics_data.values())
    
    return HTMLResponse(
        content=env.get_template("topics.html").render(
            request=request,
            topics_data=topics_data,
            total_tags=total_tags,
            total_content=total_content,
            feature_flags=get_feature_flags(),
        )
    )

async def filter_topics(request: Request):
    """Filter content by selected tags via HTMX."""
    form = await request.form()
    selected_tags = form.getlist("tags")
    
    filtered_content = ContentManager.filter_content_by_tags(selected_tags)
    
    return HTMLResponse(
        content=env.get_template("partials/topics_filter.html").render(
            request=request,
            filtered_content=filtered_content,
            selected_tags=selected_tags,
            total_results=len(filtered_content)
        )
    )

async def filter_topics_get(request: Request):
    """Filter content by selected tags via query parameters."""
    selected_tags = request.query_params.getlist("tags")
    
    filtered_content = ContentManager.filter_content_by_tags(selected_tags)
    
    return HTMLResponse(
        content=env.get_template("partials/topics_filter.html").render(
            request=request,
            filtered_content=filtered_content,
            selected_tags=selected_tags,
            total_results=len(filtered_content)
        )
    )

async def garden_paths_index(request: Request):
    """Display all available garden paths."""
    feature_flags = get_feature_flags()
    
    # Check if garden paths feature is enabled
    if not feature_flags.enable_garden_paths:
        raise HTTPException(status_code=404, detail="Garden Paths feature is not enabled")
    
    garden_paths = ContentManager.get_garden_paths()
    
    # Validate each path and add validation status
    paths_with_validation = {}
    for path_id, path_data in garden_paths.items():
        validation = ContentManager.validate_path_content(path_id)
        paths_with_validation[path_id] = {
            **path_data,
            "validation": validation,
            "id": path_id
        }
    
    return HTMLResponse(
        content=env.get_template("garden_paths.html").render(
            request=request,
            garden_paths=paths_with_validation,
            feature_flags=get_feature_flags(),
        )
    )

async def named_garden_path(request: Request, path_name: str):
    """Load a curated garden path by name and redirect to garden walk."""
    feature_flags = get_feature_flags()
    
    # Check if garden paths feature is enabled
    if not feature_flags.enable_garden_paths:
        raise HTTPException(status_code=404, detail="Garden Paths feature is not enabled")
    
    path_data = ContentManager.get_garden_path(path_name)
    
    if not path_data:
        raise HTTPException(status_code=404, detail="Garden path not found")
    
    # Validate that the path content exists
    validation = ContentManager.validate_path_content(path_name)
    
    if not validation["valid"]:
        # For now, show the path anyway but with warnings
        # In a full implementation, you might want to handle missing content differently
        pass
    
    # For now, render a simple path view - in Phase 3 this would redirect to garden-walk
    return HTMLResponse(
        content=env.get_template("garden_path.html").render(
            request=request,
            path_name=path_name,
            path_data=path_data,
            validation=validation,
            feature_flags=get_feature_flags(),
        )
    )

async def garden_path_progress(path_name: str, completed: str = ""):
    """Get progress through a garden path based on completed items."""
    feature_flags = get_feature_flags()
    
    # Check if garden paths feature is enabled
    if not feature_flags.enable_garden_paths:
        raise HTTPException(status_code=404, detail="Garden Paths feature is not enabled")
    
    completed_items = completed.split(",") if completed else []
    progress = ContentManager.get_path_progress(path_name, completed_items)
    
    if not progress or progress["total_steps"] == 0:
        raise HTTPException(status_code=404, detail="Garden path not found")
    
    return JSONResponse(content=progress)

async def get_garden_bed_items(request: Request, topic: str, expanded: bool = False):
    """Return all items for a garden bed topic (for dropdown expansion)."""
    with logfire.span("garden_bed_items", topic=topic, expanded=expanded):
        try:
            # Get all content for this topic
            garden_data = ContentManager.get_all_garden_content()
            all_content = garden_data.get("all_content", [])
            
            # Filter by topic
            topic_items = [
                item for item in all_content
                if topic.lower() in [tag.lower() for tag in item.get("tags", [])]
            ]
            
            # Sort by status priority (Evergreen > Growing > Budding > Seedling)
            status_priority = {"Evergreen": 0, "Growing": 1, "Budding": 2}
            topic_items.sort(
                key=lambda x: (
                    status_priority.get(x.get("status", "Seedling"), 3),
                    x.get("title", "")
                )
            )
            
            # Render the partial template
            template = env.get_template("partials/garden_bed_items.html")
            html_content = template.render(
                topic=topic,
                items=topic_items,
                expanded=expanded,
                request=request,
            )
            
            return HTMLResponse(content=html_content)
        except Exception as e:
            logfire.error("garden_bed_items_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

async def filter_topics_htmx(request: Request):
    """Filter content by selected topics via HTMX."""
    form = await request.form()
    selected_topics = form.getlist("topics")
    search_query = form.get("search", "").strip()
    
    with logfire.span("filter_topics", topics=selected_topics, search=search_query):
        try:
            # Get all content
            garden_data = ContentManager.get_all_garden_content()
            all_content = garden_data.get("all_content", [])
            
            # Filter by selected topics
            if selected_topics:
                filtered_content = [
                    item for item in all_content
                    if any(
                        topic.lower() in [tag.lower() for tag in item.get("tags", [])]
                        for topic in selected_topics
                    )
                ]
            else:
                filtered_content = all_content
            
            # Apply search filter if provided
            if search_query:
                query_lower = search_query.lower()
                filtered_content = [
                    item for item in filtered_content
                    if query_lower in item.get("title", "").lower()
                    or query_lower in item.get("description", "").lower()
                    or any(query_lower in tag.lower() for tag in item.get("tags", []))
                ]
            
            # Group by status
            grouped_content = {
                "Evergreen": [],
                "Growing": [],
                "Budding": [],
                "Seedling": []
            }
            
            for item in filtered_content:
                status = item.get("status", "Seedling")
                if status not in grouped_content:
                    status = "Seedling"
                grouped_content[status].append(item)
            
            # Render the filtered results
            template = env.get_template("partials/topics_filtered.html")
            html_content = template.render(
                grouped_content=grouped_content,
                selected_topics=selected_topics,
                search_query=search_query,
                total_results=len(filtered_content),
                request=request,
            )
            
            return HTMLResponse(content=html_content)
        except Exception as e:
            logfire.error("filter_topics_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

async def get_mixed_content_api(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    content_types: Optional[List[str]] = None,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Return paginated mixed content as an ``HTMLResponse``."""
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
                    next_page=result["next_page"],
                    content_length=len(result["content"]),
                    total=result["total"],
                )

            with logfire.span("rendering_template"):
                template = env.get_template("partials/mixed_content_page.html")
                html_content = template.render(
                    mixed_content=result["content"],
                    next_page=result["next_page"],
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

async def read_content(
    request: Request, 
    content_type: str, 
    page_name: str,
    content_service: IContentProvider = Depends(get_content_service),
    backlink_service: IBacklinkService = Depends(get_backlink_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer)
):
    """Render a page for ``content_type`` and ``page_name`` as ``HTMLResponse``."""
    try:
        content_data = content_service.get_content_by_slug(content_type, page_name)
        if not content_data:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get backlinks for this content
        backlinks = backlink_service.get_backlinks(page_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Content not found")
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = "partials/content.html" if is_htmx else "content_page.html"

    logfire.debug(
        "rendering_content",
        template=template_name,
        is_htmx=is_htmx,
        content_type=content_type,
        page_name=page_name,
    )

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            content=content_data["html"],
            metadata=content_data["metadata"],
            content_type=content_type,
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5),
            feature_flags=get_feature_flags(),
        )
    )

async def read_bookmarks(request: Request):
    """Return all bookmarks rendered in an ``HTMLResponse``."""
    template_name = (
        "partials/bookmarks.html"
        if request.headers.get("HX-Request") == "true"
        else "bookmarks.html"
    )
    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            bookmarks=ContentManager.get_bookmarks(
                limit=9999
            ),  # Using a large number instead of None
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5),
            feature_flags=get_feature_flags(),
        )
    )

async def read_stars(request: Request):
    """Display starred repositories from GitHub in an ``HTMLResponse``."""
    template_name = (
        "partials/stars.html"
        if request.headers.get("HX-Request") == "true"
        else "stars.html"
    )
    result = await ContentManager.get_github_stars(page=1)
    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            github_stars=result["stars"],
            next_page=result["next_page"],
            error=result["error"],
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5),
            feature_flags=get_feature_flags(),
        )
    )

async def read_stars_page(request: Request, page: int):
    """Return a single page of GitHub stars as an ``HTMLResponse``."""
    result = await ContentManager.get_github_stars(page=page)

    # If there's an error, return it with appropriate styling
    if result["error"]:
        return HTMLResponse(
            content=f'<div class="p-4 bg-red-100 text-red-700 rounded">{result["error"]}</div>',
            headers={"HX-Retarget": "#loading-indicator", "HX-Reswap": "outerHTML"},
        )

    return HTMLResponse(
        content=env.get_template("partials/stars_page.html").render(
            request=request, github_stars=result["stars"], next_page=result["next_page"]
        )
    )

async def read_til(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Render the TIL index page as an ``HTMLResponse``."""
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

async def read_til_tag(request: Request, tag: str):
    """Return TIL posts filtered by ``tag`` as an ``HTMLResponse``."""
    template_name = (
        "partials/til.html"
        if request.headers.get("HX-Request") == "true"
        else "til.html"
    )
    tils = ContentManager.get_til_posts_by_tag(tag)

    # Get all tags for the sidebar
    all_tils = ContentManager.get_til_posts(page=1)

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tils=tils,
            til_tags=all_tils["til_tags"],
            next_page=None,  # No pagination for tag views
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5),
            feature_flags=get_feature_flags(),
        )
    )

async def read_til_page(request: Request, page: int):
    """Return paginated TIL posts as an ``HTMLResponse``."""
    result = ContentManager.get_til_posts(page=page)

    return HTMLResponse(
        content=env.get_template("partials/til_page.html").render(
            request=request, tils=result["tils"], next_page=result["next_page"]
        )
    )

async def read_til_post(request: Request, til_name: str):
    """Render a single TIL post identified by ``til_name``."""
    file_path = f"{CONTENT_DIR}/til/{til_name}.md"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="TIL post not found")

    content_data = ContentManager.render_markdown(file_path)
    template_name = "content_page.html"

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            content=content_data["html"],
            metadata=content_data["metadata"],
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5),
            feature_flags=get_feature_flags(),
        )
    )

async def read_projects(request: Request):
    """Render the projects page as an ``HTMLResponse``."""
    template = env.get_template("content_page.html")
    projects_content = ContentManager.render_markdown(
        f"{CONTENT_DIR}/pages/projects.md"
    )
    return HTMLResponse(
        content=template.render(
            request=request,
            content=projects_content["html"],
            metadata=projects_content["metadata"],
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5),
            feature_flags=get_feature_flags(),
        )
    )

async def health_check():
    """Health check endpoint returning a ``JSONResponse`` with status info."""
    try:
        # Basic application health check
        return JSONResponse(
            content={
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": os.getenv("APP_VERSION", "1.0.0"),
                "environment": os.getenv("ENVIRONMENT", "production"),
            },
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
            status_code=500,
        )
