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
from .config import ai_config, content_config
from .logging_config import setup_logging, get_logger, LogConfig
from .middleware.logging_middleware import LoggingMiddleware
from .services.dependencies import get_content_service, get_path_navigation_service, get_backlink_service, get_growth_stage_renderer
from .interfaces import IContentProvider, IPathNavigationService, IBacklinkService
from .services.growth_stage_renderer import GrowthStageRenderer
from .routers import til, bookmarks, tags

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


class ContentManager:
    logger = get_logger(__name__)
    CONTENT_TYPE_MAP = {
        "bookmarks": Bookmark,
        "til": TIL,
        "notes": Note,
        "how_to": Note,  # Using Note model for how-to guides
        "pages": Note,  # Using Note model for pages
    }

    @staticmethod
    def render_markdown(file_path: str) -> dict:
        if not os.path.exists(file_path):
            return {"html": "", "metadata": {}, "errors": ["File not found"]}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML front matter and validate with Pydantic
        metadata, md_content, errors = ContentManager._parse_front_matter(
            content, file_path
        )

        # Convert and sanitize markdown
        html_content = ContentManager._convert_markdown(md_content)
        return {"html": html_content, "metadata": metadata, "errors": errors}

    @staticmethod
    def _parse_front_matter(content: str, file_path: str) -> tuple:
        errors = []
        if content.startswith("---"):
            try:
                _, fm, md_content = content.split("---", 2)
                raw_metadata = yaml.safe_load(fm)

                # Determine content type from file path
                path_parts = file_path.split(os.sep)
                content_type = path_parts[-2] if len(path_parts) > 1 else "notes"

                # Get the appropriate model
                model_class = ContentManager.CONTENT_TYPE_MAP.get(
                    content_type, BaseContent
                )

                try:
                    # Convert string dates to datetime objects
                    if isinstance(raw_metadata.get("created"), str):
                        raw_metadata["created"] = datetime.strptime(
                            raw_metadata["created"], "%Y-%m-%d"
                        )
                    if isinstance(raw_metadata.get("updated"), str):
                        raw_metadata["updated"] = datetime.strptime(
                            raw_metadata["updated"], "%Y-%m-%d"
                        )

                    # Validate with Pydantic model
                    validated_metadata = model_class(**raw_metadata)
                    return validated_metadata.model_dump(), md_content, errors
                except ValidationError as e:
                    errors.extend([f"{err['loc']}: {err['msg']}" for err in e.errors()])
                    return raw_metadata, md_content, errors

            except ValueError:
                errors.append("Invalid front matter format")
                return {}, content, errors
            except yaml.YAMLError as e:
                errors.append(f"YAML parsing error: {str(e)}")
                return {}, content, errors

        errors.append("No front matter found")
        return {}, content, errors

    @staticmethod
    def _convert_markdown(content: str) -> str:
        # Create a custom extension to wrap inline code in spans
        class InlineCodeExtension(markdown.Extension):
            def extendMarkdown(self, md):
                # Override the inline code pattern
                md.inlinePatterns.register(
                    InlineCodePattern(r"(?<!\\)(`+)(.+?)(?<!`)\1(?!`)", md),
                    "backtick",
                    175,
                )

        class InlineCodePattern(markdown.inlinepatterns.Pattern):
            def handleMatch(self, m):
                el = markdown.util.etree.Element("span")
                el.set("class", "inline-code")
                code = markdown.util.etree.SubElement(el, "code")
                code.text = markdown.util.AtomicString(m.group(2))
                return el

        # Custom FencedCode extension to preserve link styling
        class CustomFencedCodeExtension(FencedCodeExtension):
            def extendMarkdown(self, md):
                """Add FencedBlockPreprocessor to the Markdown instance."""
                md.registerExtension(self)
                config = self.getConfigs()
                processor = markdown.extensions.fenced_code.FencedBlockPreprocessor(
                    md, config
                )
                processor.run = lambda lines: self.custom_run(
                    processor, lines
                )  # Override the run method
                md.preprocessors.register(processor, "fenced_code_block", 25)

            def custom_run(self, processor, lines):
                """Custom run method to preserve link styling within code blocks"""
                new_lines = []
                for line in lines:
                    if line.strip().startswith("```"):
                        new_lines.append(line)
                    else:
                        # Replace markdown links with HTML links that have our styling
                        line = re.sub(
                            r"\[(.*?)\]\((.*?)\)",
                            r'<a href="\2" class="text-emerald-600 hover:text-emerald-500 hover:underline">\1</a>',
                            line,
                        )
                        new_lines.append(line)
                return processor.__class__.run(processor, new_lines)

        md = markdown.Markdown(
            extensions=[
                "extra",
                "admonition",
                TocExtension(baselevel=1),
                CustomFencedCodeExtension(),
                InlineCodeExtension(),
            ]
        )

        html_content = md.convert(content)

        # Use BeautifulSoup to modify link styles
        soup = BeautifulSoup(html_content, "html.parser")
        for link in soup.find_all("a"):
            existing_classes = link.get("class", [])
            if isinstance(existing_classes, str):
                existing_classes = existing_classes.split()
            new_classes = existing_classes + [
                "text-emerald-600",
                "hover:text-emerald-500",
                "hover:underline",
            ]
            link["class"] = " ".join(new_classes)

        # Update ALLOWED_ATTRIBUTES to ensure classes survive sanitization
        allowed_attrs = {
            **ALLOWED_ATTRIBUTES,
            "a": ["href", "title", "rel", "class", "target"],
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

        clean_html = bleach.clean(
            str(soup), tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True
        )

        return clean_html

    @staticmethod
    def get_content(content_type: str, limit=None):
        """Get content of a specific type with consistent format"""
        files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        content = []
        validation_errors = {}

        for file in files:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]
            errors = file_content.get("errors", [])

            if errors:
                validation_errors[str(file)] = errors
                # Skip invalid content in production, include with errors in development
                if os.getenv("ENVIRONMENT") == "production":
                    continue

            # Get excerpt
            soup = BeautifulSoup(file_content["html"], "html.parser")
            first_p = soup.find("p")
            excerpt = first_p.get_text() if first_p else ""

            # Create consistent content item structure
            # Convert datetime objects in metadata to strings
            def convert_dates_in_dict(obj):
                if isinstance(obj, dict):
                    return {k: convert_dates_in_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dates_in_dict(item) for item in obj]
                elif isinstance(obj, datetime):
                    return obj.strftime("%Y-%m-%d")
                else:
                    return obj
            
            # Clean metadata of datetime objects
            clean_metadata = convert_dates_in_dict(metadata)
            
            content_item = {
                "name": name,
                "title": clean_metadata.get("title", name.replace("-", " ").title()),
                "created": clean_metadata.get("created", ""),
                "updated": clean_metadata.get("updated", ""),
                "metadata": clean_metadata,
                "excerpt": excerpt,
                "url": f"/{content_type}/{name}",
                "content_type": content_type,
                "type_indicator": {
                    "notes": "Note",
                    "how_to": "How To",
                    "bookmarks": "Bookmark",
                    "til": "TIL",
                }.get(content_type, ""),
                "html": file_content["html"],
            }

            if errors and os.getenv("ENVIRONMENT") != "production":
                content_item["validation_errors"] = errors

            content.append(content_item)

        # Log validation errors
        if validation_errors:
            logfire.warn(
                "content_validation_errors",
                content_type=content_type,
                errors=validation_errors,
            )

        return {
            "content": content[:limit] if limit else content,
            "total": len(content),
            "type": content_type,
        }

    @staticmethod
    def _get_date_from_filename(filename: str | Path) -> str:
        match = re.search(r'(\d{4}-\d{2}-\d{2})', Path(filename).name)
        return match.group(1) if match else '0000-00-00'

    @staticmethod
    def get_random_quote():
        quote_files = list(Path(CONTENT_DIR, "notes").glob("*quoting*.md"))
        if not quote_files:
            return None

        random_quote_file = random.choice(quote_files)
        quote_content = ContentManager.render_markdown(str(random_quote_file))

        # Extract quote safely
        soup = BeautifulSoup(quote_content["html"], "html.parser")
        blockquote = soup.find("blockquote")
        quote_text = blockquote.get_text() if blockquote else ""

        return {
            "text": quote_text,
            "author": quote_content["metadata"].get("author", quote_content["metadata"].get("title", "")),
        }

    @staticmethod
    def get_bookmarks(limit: Optional[int] = 10) -> List[dict]:
        """Get bookmarks with pagination"""
        files = list(Path(CONTENT_DIR, "bookmarks").glob("*.md"))
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)
        bookmarks = []
        files_to_process = (
            files if limit is None else sorted(files, reverse=True)[:limit]
        )

        for file in files_to_process:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]

            # Convert the metadata to a Bookmark model for validation
            try:
                bookmark = Bookmark(**metadata)
                bookmarks.append(
                    {
                        "name": name,
                        "title": bookmark.title,
                        "url": bookmark.url,
                        "created": bookmark.created,
                        "updated": bookmark.updated,
                        "tags": bookmark.tags,
                        "description": bookmark.description,
                        "via_url": bookmark.via_url,
                        "via_title": bookmark.via_title,
                        "commentary": bookmark.commentary,
                        "screenshot_path": bookmark.screenshot_path,
                        "author": bookmark.author,
                        "source": bookmark.source,
                    }
                )
            except ValidationError as e:
                logfire.error(
                    "bookmark_validation_error", bookmark_name=name, error=str(e)
                )
                continue

        return bookmarks

    @staticmethod
    def get_posts_by_tag(tag: str, content_types: List[str] = None):
        posts = []
        if content_types is None:
            content_types = ["notes", "how_to", "til"]

        for content_type in content_types:
            files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
            for file in files:
                name = file.stem
                file_content = ContentManager.render_markdown(str(file))
                metadata = file_content["metadata"]

                if "tags" in metadata and tag in metadata["tags"]:
                    # Get excerpt for all post types
                    soup = BeautifulSoup(file_content["html"], "html.parser")
                    first_p = soup.find("p")
                    excerpt = first_p.get_text() if first_p else ""

                    posts.append(
                        {
                            "type": content_type,
                            "name": name,
                            "title": metadata.get(
                                "title", name.replace("-", " ").title()
                            ),
                            "created": metadata.get("created", ""),
                            "updated": metadata.get("updated", ""),
                            "metadata": metadata,
                            "excerpt": excerpt,
                            "url": f"/{content_type}/{name}",
                        }
                    )

        return sorted(posts, key=lambda x: x.get("created", ""), reverse=True)

    @staticmethod
    @staticmethod
    @timed_lru_cache(maxsize=1, ttl_seconds=3600)
    async def get_github_stars(page: int = 1, per_page: int = 30) -> dict:
        """
        Fetch starred GitHub repositories asynchronously with pagination.
        Returns both the stars and pagination info.
        Handles rate limiting gracefully.
        """
        try:
            response = await http_client.get(
                f"https://api.github.com/users/{ai_config.github_username or GITHUB_USERNAME}/starred",
                params={
                    "page": page,
                    "per_page": per_page
                })

            # Handle rate limiting
            if (
                response.status_code == 403
                and "X-RateLimit-Remaining" in response.headers
            ):
                remaining = int(response.headers["X-RateLimit-Remaining"])
                reset_time = int(response.headers["X-RateLimit-Reset"])
                if remaining == 0:
                    reset_datetime = datetime.fromtimestamp(reset_time)
                    logfire.warn(
                        "github_rate_limit_exceeded",
                        reset_time=reset_datetime.isoformat(),
                    )
                    return {
                        "stars": [],
                        "next_page": None,
                        "error": "Rate limit exceeded. Please try again later.",
                    }

            if response.status_code != 200:
                logfire.error(
                    "github_api_error",
                    status_code=response.status_code,
                    response_text=response.text,
                )
                return {
                    "stars": [],
                    "next_page": None,
                    "error": f"GitHub API error: {response.status_code}",
                }

            # Parse Link header for pagination info
            link_header = response.headers.get("Link", "")
            next_page = None
            if link_header:
                links = {}
                for part in link_header.split(","):
                    section = part.split(";")
                    url = section[0].strip()[1:-1]
                    for attr in section[1:]:
                        if "rel=" in attr:
                            rel = attr.split("=")[1].strip('"')
                            links[rel] = url

                if "next" in links:
                    next_page = page + 1

            stars = []
            for repo in response.json():
                stars.append(
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo["description"],
                        "html_url": repo["html_url"],  # Changed from "url" to "html_url"
                        "language": repo["language"],
                        "stargazers_count": repo["stargazers_count"],  # Changed from "stars"
                        "forks_count": repo.get("forks_count", 0),  # Added forks_count
                        "starred_at": datetime.strptime(
                            repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ).strftime("%Y-%m-%d"),
                    }
                )

            return {"stars": stars, "next_page": next_page, "error": None}

        except httpx.RequestError as e:
            logfire.error("github_request_error", error=str(e))
            return {
                "stars": [],
                "next_page": None,
                "error": "Failed to fetch GitHub stars",
            }

    @staticmethod
    def ttl_hash(seconds=3600):
        """Return the same value within `seconds` time period"""
        return round(datetime.now().timestamp() / seconds)
    
    @staticmethod
    def get_tag_counts() -> Dict[str, int]:
        """Get counts of content items by tag."""
        tag_counts = {}
        content_types = ["bookmarks", "til", "notes", "how_to"]
        
        for content_type in content_types:
            files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
            for file in files:
                file_content = ContentManager.render_markdown(str(file))
                metadata = file_content["metadata"]
                for tag in metadata.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return tag_counts
    
    @staticmethod
    def get_topics_data() -> Dict[str, Any]:
        """Get organized topics data with garden bed clustering."""
        from app.config import get_config
        config = get_config()
        
        tag_counts = ContentManager.get_tag_counts()
        garden_beds = config["garden_beds"]
        
        # Organize tags into garden beds
        bed_data = {}
        uncategorized_tags = set(tag_counts.keys())
        
        for bed_name, bed_config in garden_beds.items():
            bed_tags = []
            for tag in bed_config["tags"]:
                if tag in tag_counts:
                    bed_tags.append({
                        "name": tag,
                        "count": tag_counts[tag]
                    })
                    uncategorized_tags.discard(tag)
            
            if bed_tags:
                bed_data[bed_name] = {
                    "tags": sorted(bed_tags, key=lambda x: x["count"], reverse=True),
                    "color": bed_config["color"],
                    "icon": bed_config["icon"],
                    "total_count": sum(tag["count"] for tag in bed_tags)
                }
        
        # Add uncategorized tags if any
        if uncategorized_tags:
            uncategorized = [{
                "name": tag,
                "count": tag_counts[tag]
            } for tag in uncategorized_tags]
            bed_data["Other"] = {
                "tags": sorted(uncategorized, key=lambda x: x["count"], reverse=True),
                "color": "bg-gray-100 text-gray-800 border-gray-200",
                "icon": "🏷️",
                "total_count": sum(tag["count"] for tag in uncategorized)
            }
        
        return bed_data
    
    @staticmethod
    def filter_content_by_tags(selected_tags: List[str]) -> List[Dict[str, Any]]:
        """Filter mixed content by selected tags."""
        if not selected_tags:
            return []
        
        filtered_content = []
        selected_tags_set = set(selected_tags)
        content_types = ["bookmarks", "til", "notes", "how_to"]
        
        for content_type in content_types:
            files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
            for file in files:
                name = file.stem
                file_content = ContentManager.render_markdown(str(file))
                metadata = file_content["metadata"]
                
                # Check if content has any of the selected tags
                if selected_tags_set.intersection(set(metadata.get("tags", []))):
                    # Get excerpt
                    soup = BeautifulSoup(file_content["html"], "html.parser")
                    first_p = soup.find("p")
                    excerpt = first_p.get_text() if first_p else ""
                    
                    filtered_content.append({
                        "type": content_type,
                        "title": metadata.get("title", name.replace("-", " ").title()),
                        "slug": name,
                        "created": metadata.get("created", ""),
                        "updated": metadata.get("updated", ""),
                        "tags": metadata.get("tags", []),
                        "status": metadata.get("status", "Evergreen"),
                        "description": metadata.get("description", excerpt),
                        "url": metadata.get("url", None),
                        "difficulty": metadata.get("difficulty", None)
                    })
        
        # Sort by creation date, newest first
        filtered_content.sort(key=lambda x: x["created"] if x["created"] else "", reverse=True)
        return filtered_content
    
    @staticmethod 
    def get_garden_paths() -> Dict[str, Any]:
        """Get all available garden paths."""
        from app.config import get_config
        config = get_config()
        return config["garden_paths"]
    
    @staticmethod
    def get_garden_path(path_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific garden path by ID."""
        garden_paths = ContentManager.get_garden_paths()
        return garden_paths.get(path_id)
    
    @staticmethod
    def get_path_progress(path_id: str, content_items: List[str]) -> Dict[str, Any]:
        """Calculate progress through a garden path."""
        path_data = ContentManager.get_garden_path(path_id)
        if not path_data:
            return {"progress": 0, "current_step": 0, "total_steps": 0, "completed_items": []}
        
        path_items = path_data["path"]
        completed_items = [item for item in path_items if item in content_items]
        
        return {
            "progress": int((len(completed_items) / len(path_items)) * 100) if path_items else 0,
            "current_step": len(completed_items),
            "total_steps": len(path_items),
            "completed_items": completed_items,
            "next_item": path_items[len(completed_items)] if len(completed_items) < len(path_items) else None
        }
    
    @staticmethod
    def validate_path_content(path_id: str) -> Dict[str, Any]:
        """Validate that all content in a garden path exists."""
        path_data = ContentManager.get_garden_path(path_id)
        if not path_data:
            return {"valid": False, "missing": [], "existing": []}
        
        missing_items = []
        existing_items = []
        
        for item_id in path_data["path"]:
            # Check if content exists in any content type directory
            found = False
            content_types = ["notes", "how_to", "til", "bookmarks"]
            
            for content_type in content_types:
                file_path = Path(CONTENT_DIR, content_type, f"{item_id}.md")
                if file_path.exists():
                    existing_items.append({
                        "id": item_id,
                        "type": content_type,
                        "path": str(file_path)
                    })
                    found = True
                    break
            
            if not found:
                missing_items.append(item_id)
        
        return {
            "valid": len(missing_items) == 0,
            "missing": missing_items,
            "existing": existing_items,
            "path_name": path_data["name"],
            "path_description": path_data["description"]
        }

    @staticmethod
    def get_til_posts(page: int = 1, per_page: int = 30) -> dict:
        """Get TiL posts with pagination"""
        files = list(Path(CONTENT_DIR, "til").glob("*.md"))
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_files = files[start_idx:end_idx]

        tils = []
        til_tags = {}

        for file in page_files:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]

            # Get first paragraph for excerpt
            soup = BeautifulSoup(file_content["html"], "html.parser")
            first_p = soup.find("p")
            excerpt = first_p.get_text() if first_p else ""

            # Update tag counts
            for tag in metadata.get("tags", []):
                til_tags[tag] = til_tags.get(tag, 0) + 1

            tils.append(
                {
                    "name": name,
                    "title": metadata.get("title", name.replace("-", " ").title()),
                    "created": metadata.get("created", ""),
                    "updated": metadata.get("updated", ""),
                    "tags": metadata.get("tags", []),
                    "status": metadata.get("status", "Evergreen"),
                    "excerpt": excerpt,
                    "url": f"/til/{name}",
                }
            )

        return {
            "tils": tils,
            "til_tags": til_tags,
            "next_page": page + 1 if end_idx < len(files) else None,
        }

    @staticmethod
    def get_til_posts_by_tag(tag: str) -> List[dict]:
        """Get TiL posts filtered by tag"""
        files = list(Path(CONTENT_DIR, "til").glob("*.md"))
        tils = []

        for file in files:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]

            if tag in metadata.get("tags", []):
                soup = BeautifulSoup(file_content["html"], "html.parser")
                first_p = soup.find("p")
                excerpt = first_p.get_text() if first_p else ""

                tils.append(
                    {
                        "name": name,
                        "title": metadata.get("title", name.replace("-", " ").title()),
                        "created": metadata.get("created", ""),
                        "updated": metadata.get("updated", ""),
                        "tags": metadata.get("tags", []),
                        "status": metadata.get("status", "Evergreen"),
                        "excerpt": excerpt,
                        "url": f"/til/{name}",
                    }
                )

        return sorted(tils, key=lambda x: x["created"], reverse=True)

    @staticmethod
    @timed_lru_cache(maxsize=10, ttl_seconds=300)  # Cache for 5 minutes
    async def get_mixed_content(page: int = 1, per_page: int = 10) -> dict:
        """Get mixed content (notes, how-tos, bookmarks, TILs) sorted by date"""
        try:
            all_content = []
            errors = []

            # Get content from different sections
            try:
                notes = ContentManager.get_content("notes")["content"]
            except Exception as e:
                errors.append(f"Error fetching notes: {str(e)}")
                notes = []

            try:
                how_tos = ContentManager.get_content("how_to")["content"]
            except Exception as e:
                errors.append(f"Error fetching how-tos: {str(e)}")
                how_tos = []

            try:
                bookmarks = ContentManager.get_bookmarks()
            except Exception as e:
                errors.append(f"Error fetching bookmarks: {str(e)}")
                bookmarks = []

            try:
                til_result = ContentManager.get_til_posts(page=1, per_page=9999)
                tils = til_result["tils"]
            except Exception as e:
                errors.append(f"Error fetching TILs: {str(e)}")
                tils = []

            # Process and normalize content
            def process_content(items, content_type):
                for item in items:
                    try:
                        # Ensure consistent metadata structure
                        if "metadata" not in item and content_type in [
                            "bookmarks",
                            "til",
                        ]:
                            item["metadata"] = {
                                "title": item.get("title", ""),
                                "created": item.get("created", ""),
                                "updated": item.get("updated", ""),
                                "tags": item.get("tags", []),
                            }

                        # Generate excerpt if not present
                        if "excerpt" not in item and "html" in item:
                            soup = BeautifulSoup(item["html"], "html.parser")
                            first_p = soup.find("p")
                            item["excerpt"] = first_p.get_text() if first_p else ""

                        # Add content type and normalize URL
                        item["content_type"] = content_type
                        if "url" not in item:
                            item["url"] = f"/{content_type}/{item['name']}"

                        # Add type indicator for display
                        item["type_indicator"] = {
                            "notes": "Note",
                            "how_to": "How To",
                            "bookmarks": "Bookmark",
                            "til": "TIL",
                        }.get(content_type, "")

                        all_content.append(item)
                    except Exception as e:
                        errors.append(f"Error processing {content_type} item: {str(e)}")

            # Process each content type
            process_content(notes, "notes")
            process_content(how_tos, "how_to")
            process_content(bookmarks, "bookmarks")
            process_content(tils, "til")

            # Sort all content by date
            def get_date(item):
                # Try different date locations
                date = item.get("created", None)
                if not date:
                    date = item.get("metadata", {}).get("created", None)

                if isinstance(date, str):
                    try:
                        return datetime.strptime(date, "%Y-%m-%d")
                    except ValueError:
                        return datetime.min
                return date or datetime.min

            all_content.sort(key=get_date, reverse=True)

            # Calculate pagination
            if page < 1:
                raise ValueError("Page number must be greater than 0")
            if per_page < 1:
                raise ValueError("Items per page must be greater than 0")

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page

            if start_idx >= len(all_content):
                return {
                    "content": [],
                    "next_page": None,
                    "total": len(all_content),
                    "current_page": page,
                    "total_pages": (len(all_content) + per_page - 1) // per_page,
                    "errors": errors,
                }

            has_more = end_idx < len(all_content)

            return {
                "content": all_content[start_idx:end_idx],
                "next_page": page + 1 if has_more else None,
                "total": len(all_content),
                "current_page": page,
                "total_pages": (len(all_content) + per_page - 1) // per_page,
                "errors": errors,
            }

        except Exception as e:
            raise ValueError(f"Error retrieving mixed content: {str(e)}")
    
    @staticmethod
    def get_all_garden_content() -> Dict[str, Any]:
        """Get all content for the filterable garden homepage."""
        all_content = []
        all_tags = set()
        
        def convert_date_to_string(date_value):
            """Convert datetime objects to strings."""
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d")
            return date_value or ""
        
        # Get content from each type
        notes_result = ContentManager.get_content("notes")
        notes = notes_result["content"] if isinstance(notes_result, dict) else notes_result
        
        how_tos_result = ContentManager.get_content("how_to")
        how_tos = how_tos_result["content"] if isinstance(how_tos_result, dict) else how_tos_result
        
        til_result = ContentManager.get_til_posts(page=1, per_page=9999)
        tils = til_result["tils"]
        
        bookmarks = ContentManager.get_bookmarks(limit=None)
        
        # Process and combine all content
        for note in notes:
            if note.get("metadata", {}).get("status") != "draft":
                note["content_type"] = "notes"
                note["type_label"] = "Note"
                note["growth_stage"] = note.get("metadata", {}).get("status", "Seedling")
                note["tags"] = note.get("metadata", {}).get("tags", [])
                note["created"] = convert_date_to_string(note.get("metadata", {}).get("created", note.get("created", "")))
                note["updated"] = convert_date_to_string(note.get("metadata", {}).get("updated", note.get("updated", "")))
                all_content.append(note)
                all_tags.update(note["tags"])
        
        for how_to in how_tos:
            if how_to.get("metadata", {}).get("status") != "draft":
                how_to["content_type"] = "how_to"
                how_to["type_label"] = "How-To"
                how_to["growth_stage"] = how_to.get("metadata", {}).get("status", "Seedling")
                how_to["tags"] = how_to.get("metadata", {}).get("tags", [])
                how_to["created"] = convert_date_to_string(how_to.get("metadata", {}).get("created", how_to.get("created", "")))
                how_to["updated"] = convert_date_to_string(how_to.get("metadata", {}).get("updated", how_to.get("updated", "")))
                all_content.append(how_to)
                all_tags.update(how_to["tags"])
                
        for til in tils:
            # TILs don't have metadata wrapper, status is at top level
            if til.get("status") != "draft":
                til["content_type"] = "til"
                til["type_label"] = "TIL"
                til["growth_stage"] = til.get("status", "Seedling")
                # Add slug field for TILs
                if 'name' in til and 'slug' not in til:
                    til['slug'] = til['name']
                # Convert dates for TILs
                til["created"] = convert_date_to_string(til.get("created", ""))
                til["updated"] = convert_date_to_string(til.get("updated", ""))
                all_content.append(til)
                all_tags.update(til.get("tags", []))
                
        for bookmark in bookmarks:
            # Bookmarks don't have metadata wrapper, status is at top level
            if bookmark.get("status") != "draft":
                bookmark["content_type"] = "bookmarks"
                bookmark["type_label"] = "Bookmark"
                bookmark["growth_stage"] = bookmark.get("status", "Seedling")
                # Convert dates for bookmarks
                bookmark["created"] = convert_date_to_string(bookmark.get("created", ""))
                bookmark["updated"] = convert_date_to_string(bookmark.get("updated", ""))
                all_content.append(bookmark)
                all_tags.update(bookmark.get("tags", []))
        
        # Sort by creation date (newest first)
        all_content.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        # Get unique growth stages
        growth_stages = list(set(item.get("growth_stage", "Seedling") for item in all_content))
        
        # Get unique content types
        content_types = list(set(item.get("type_label", "") for item in all_content))
        
        return {
            "content": all_content,
            "tags": sorted(list(all_tags)),
            "growth_stages": sorted(growth_stages),
            "content_types": sorted(content_types),
            "total_count": len(all_content)
        }
    
    @staticmethod
    @timed_lru_cache(maxsize=1, ttl_seconds=300)
    async def get_homepage_sections() -> Dict[str, Any]:
        """Get structured content sections for the topographical homepage."""
        from collections import defaultdict
        
        # Get all published content
        all_content = []
        
        # Get content from each type
        notes_result = ContentManager.get_content("notes")
        notes = notes_result["content"] if isinstance(notes_result, dict) else notes_result
        
        how_tos_result = ContentManager.get_content("how_to")
        how_tos = how_tos_result["content"] if isinstance(how_tos_result, dict) else how_tos_result
        
        til_result = ContentManager.get_til_posts(page=1, per_page=9999)
        tils = til_result["tils"]
        
        bookmarks = ContentManager.get_bookmarks(limit=None)
        
        # Combine all content
        for note in notes:
            if note.get("status") != "draft":
                note["content_type"] = "notes"
                all_content.append(note)
        
        for how_to in how_tos:
            if how_to.get("status") != "draft":
                how_to["content_type"] = "how_to"
                all_content.append(how_to)
                
        for til in tils:
            if til.get("status") != "draft":
                til["content_type"] = "til"
                all_content.append(til)
                
        for bookmark in bookmarks:
            if bookmark.get("status") != "draft":
                bookmark["content_type"] = "bookmarks"
                all_content.append(bookmark)
        
        sections = {
            'garden_beds': {},
            'recently_tended': [],
            'featured': [],
            'recent_posts': [],
            'github_stars': [],
            'random_quote': None
        }
        
        # Get recent posts (all content sorted by date)
        recent_posts = sorted(
            [item for item in all_content if item.get('status') != 'draft' and item.get('content_type') in ['notes', 'how_to', 'til']],
            key=lambda x: x.get('created', ''),
            reverse=True
        )[:10]  # Get 10 most recent posts
        
        # Add slug field (mapping from name) for template compatibility
        for post in recent_posts:
            if 'name' in post and 'slug' not in post:
                post['slug'] = post['name']
        
        sections['recent_posts'] = recent_posts
        
        # Get GitHub stars (top 5)
        try:
            github_result = await ContentManager.get_github_stars(page=1, per_page=5)
            sections['github_stars'] = github_result.get('stars', [])[:5]
        except Exception:
            sections['github_stars'] = []
        
        # Get random quote
        sections['random_quote'] = ContentManager.get_random_quote()
        
        # Calculate cutoff for recently tended (30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Group content by topics for garden beds
        topic_groups = defaultdict(list)
        
        for item in all_content:
            # Skip draft content
            if item.get('status') == 'draft':
                continue
                
            # Check if recently tended (updated in last 30 days)
            updated_str = item.get('updated', item.get('created', ''))
            if updated_str:
                try:
                    if isinstance(updated_str, str):
                        updated_date = datetime.strptime(updated_str, '%Y-%m-%d')
                    else:
                        updated_date = updated_str
                    if updated_date.replace(tzinfo=None) > thirty_days_ago:
                        sections['recently_tended'].append(item)
                except (ValueError, TypeError, AttributeError):
                    pass
            
            # Group by tags for garden beds
            tags = item.get('tags', [])
            if tags:
                primary_tag = tags[0]  # Use first tag as primary grouping
                topic_groups[primary_tag].append(item)
        
        # Convert topic groups to garden beds
        sections['garden_beds'] = dict(topic_groups)
        
        # Sort recently tended by updated date (most recent first)
        sections['recently_tended'].sort(
            key=lambda x: x.get('updated', x.get('created', '')), 
            reverse=True
        )
        
        # Limit recently tended to reasonable number
        sections['recently_tended'] = sections['recently_tended'][:6]  # Reduced to 6 to make room
        
        # For featured content, take a few high-quality items
        # Priority: Evergreen status, then by creation date
        featured_candidates = [
            item for item in all_content 
            if item.get('status') not in ['draft', 'Budding']
        ]
        featured_candidates.sort(
            key=lambda x: (
                x.get('status') == 'Evergreen',  # Evergreen first
                x.get('created', '')  # Then by date
            ), 
            reverse=True
        )
        sections['featured'] = featured_candidates[:3]  # Top 3
        
        return sections


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
    rss += f'<link>{content_config.base_url}</link>\n'
    rss += '<description>Latest content from An Oliphant Never Forgets</description>\n'
    rss += '<language>en-us</language>\n'
    rss += '<managingEditor>joshua.oliphant@gmail.com (Joshua Oliphant)</managingEditor>\n'
    rss += '<webMaster>joshua.oliphant@gmail.com (Joshua Oliphant)</webMaster>\n'
    rss += f'<atom:link href="{content_config.base_url}/feed.xml" rel="self" type="application/rss+xml" />\n'

    for item, content_type in all_content:
        rss += "<item>\n"
        rss += f'<title>{item["title"]}</title>\n'
        rss += f'<link>{content_config.base_url}/{content_type}/{item["name"]}</link>\n'
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

        rss += f'<guid>{content_config.base_url}/{content_type}/{item["name"]}</guid>\n'
        rss += '</item>\n'

    rss += "</channel>\n"
    rss += "</rss>"

    return rss


def generate_sitemap() -> str:
    """Generate XML sitemap for the site"""
    # Base URL for the site
    base_url = content_config.base_url
    
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


@app.get("/feed.xml")
@app.get("/feed")
async def rss_feed():
    """Return the RSS feed as an XML ``Response``."""
    rss_content = generate_rss_feed()
    return Response(content=rss_content, media_type="application/xml")


@app.get("/sitemap.xml")
async def sitemap():
    """Serve the XML sitemap as an XML ``Response``."""
    sitemap_content = generate_sitemap()
    return Response(content=sitemap_content, media_type="application/xml")


@app.get("/robots.txt")
async def robots():
    """Return ``robots.txt`` as a plain text ``Response``."""
    return Response(
        content=f"""User-agent: *
Allow: /
Sitemap: {content_config.base_url}/sitemap.xml""",
        media_type="text/plain"
    )


# Route handlers
@app.get("/", response_class=HTMLResponse)
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


@app.get("/garden", response_class=HTMLResponse)
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


@app.get("/explore", response_class=HTMLResponse)
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


@app.get("/now", response_class=HTMLResponse)
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


@app.get("/tags/{tag}", response_class=HTMLResponse)
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


@app.get("/topics", response_class=HTMLResponse)
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


@app.post("/topics/filter", response_class=HTMLResponse)
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


@app.get("/topics/filter", response_class=HTMLResponse)
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


@app.get("/garden-paths", response_class=HTMLResponse)
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


@app.get("/garden-path/{path_name}", response_class=HTMLResponse) 
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


@app.get("/api/garden-path/{path_name}/progress")
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



@app.get("/api/garden-bed/{topic}/items", response_class=HTMLResponse)
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


@app.post("/api/topics/filter", response_class=HTMLResponse)
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


@app.get("/api/mixed-content", response_class=HTMLResponse)
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


@app.get("/{content_type}/{page_name}", response_class=HTMLResponse)
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


@app.get("/bookmarks", response_class=HTMLResponse)
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


@app.get("/stars", response_class=HTMLResponse)
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


@app.get("/stars/page/{page}", response_class=HTMLResponse)
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


@app.get("/til", response_class=HTMLResponse)
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


@app.get("/til/tag/{tag}", response_class=HTMLResponse)
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


@app.get("/til/page/{page}", response_class=HTMLResponse)
async def read_til_page(request: Request, page: int):
    """Return paginated TIL posts as an ``HTMLResponse``."""
    result = ContentManager.get_til_posts(page=page)

    return HTMLResponse(
        content=env.get_template("partials/til_page.html").render(
            request=request, tils=result["tils"], next_page=result["next_page"]
        )
    )


@app.get("/til/{til_name}", response_class=HTMLResponse)
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


@app.get("/projects", response_class=HTMLResponse)
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


@app.get("/health")
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
