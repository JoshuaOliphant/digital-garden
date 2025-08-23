from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from contextlib import asynccontextmanager
from app.config import get_feature_flags
import os
from pathlib import Path
import httpx
import time
import uuid
import traceback
from datetime import datetime
from typing import Dict, Any, TypeVar, Callable, Awaitable
from functools import wraps
from email.utils import format_datetime
import logfire

from .config import CONTENT_DIR, TEMPLATE_DIR, STATIC_DIR, SITE_URL
from .logging_config import setup_logging, LogConfig
from .middleware.logging_middleware import LoggingMiddleware
from .services.dependencies import get_content_service, get_growth_stage_renderer
from .routers import til, bookmarks, tags, garden, pages, api, content, feeds, explore
from .content_manager import ContentManager

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

# Custom exception handlers for user-friendly error pages
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors with custom template."""
    # Check if this is an API request or HTMX request that expects JSON
    if request.url.path.startswith("/api/") or request.headers.get("Accept") == "application/json":
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc.detail) if hasattr(exc, 'detail') else "Not found"}
        )
    
    # Get some recent content for the 404 page
    try:
        content_service = get_content_service()
        all_content = content_service.get_all_content()
        recent_content = sorted(all_content, key=lambda x: x.get("updated", x.get("created", "")), reverse=True)[:5]
        
        # Add growth symbols if available
        growth_renderer = get_growth_stage_renderer()
        for item in recent_content:
            growth_stage = item.get("growth_stage", "seedling")
            item["growth_symbol"] = growth_renderer.render_stage_symbol(growth_stage)
    except Exception:
        recent_content = []
    
    # Render the 404 template
    template = env.get_template("404.html")
    html_content = template.render(
        request=request,
        recent_content=recent_content,
        debug_mode=os.getenv("ENVIRONMENT") != "production",
        error_detail=str(exc.detail) if hasattr(exc, 'detail') else None
    )
    return HTMLResponse(content=html_content, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Handle 500 errors with custom template."""
    # Generate error ID for tracking
    error_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()
    
    # Log the error with Logfire
    logfire.error(
        "server_error",
        error_id=error_id,
        path=request.url.path,
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=traceback.format_exc() if os.getenv("ENVIRONMENT") != "production" else None
    )
    
    # Check if this is an API request that expects JSON
    if request.url.path.startswith("/api/") or request.headers.get("Accept") == "application/json":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_id": error_id,
                "timestamp": timestamp
            }
        )
    
    # Render the 500 template
    template = env.get_template("500.html")
    html_content = template.render(
        request=request,
        error_id=error_id,
        timestamp=timestamp,
        debug_mode=os.getenv("ENVIRONMENT") != "production",
        error_type=type(exc).__name__ if os.getenv("ENVIRONMENT") != "production" else None,
        error_message=str(exc) if os.getenv("ENVIRONMENT") != "production" else None,
        traceback=traceback.format_exc() if os.getenv("ENVIRONMENT") != "production" else None,
        github_username="joshuaoliphant"  # You can make this configurable
    )
    return HTMLResponse(content=html_content, status_code=500)

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