from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from bs4 import BeautifulSoup
from contextlib import asynccontextmanager
import markdown
import os
import re
import yaml
import glob
import bleach
import random
import httpx
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, TypeVar, Callable, Awaitable, Union
from functools import wraps
from fastapi.responses import Response
from email.utils import format_datetime
from pydantic import ValidationError
import logfire

from .config import content_config

from .models import BaseContent, Bookmark, TIL, Note, ContentMetadata
from .config import ai_config

# Constants
CONTENT_DIR = "app/content"
TEMPLATE_DIR = "app/templates"
STATIC_DIR = "app/static"

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "ul",
    "ol", "li", "strong", "em", "a", "img", "table", "thead", "tbody", "tr",
    "th", "td", "span", "iframe"
]

ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel", "class"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
    "code": ["class"],
    "span": ["class"],
    "iframe": ["src", "width", "height", "frameborder", "allow", "allowfullscreen", "title", "referrerpolicy"]
}

T = TypeVar('T')

# Initialize HTTP client first since it's used in lifespan
http_client = httpx.AsyncClient(
    timeout=10.0, headers={"Accept": "application/vnd.github.v3+json"})

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to do here
    yield
    # Shutdown: close the HTTP client
    await http_client.aclose()

# Initialize FastAPI
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Configure Logfire with proper token validation
logfire_token = os.getenv('LOGFIRE_TOKEN')
if not logfire_token:
    if os.getenv('ENVIRONMENT') == 'production':
        raise RuntimeError("LOGFIRE_TOKEN environment variable is required in production")
    print("Warning: LOGFIRE_TOKEN not set. Running without logging in development mode.")
else:
    try:
        # Basic token format validation (assuming it should be a non-empty string of reasonable length)
        if not isinstance(logfire_token, str) or len(logfire_token) < 32:
            raise ValueError("Invalid Logfire token format")
            
        logfire.configure(
            console=logfire.ConsoleOptions(
                min_log_level='info' if os.getenv('ENVIRONMENT') == 'production' else 'debug'
            ),
            token=logfire_token
        )
        
        # Test the configuration
        logfire.info("Logfire configured successfully", 
                    environment=os.getenv('ENVIRONMENT', 'development'))
        
        # Initialize FastAPI instrumentation only if Logfire is properly configured
        logfire.instrument_fastapi(app)
        logfire.instrument_httpx()
        logfire.instrument_pydantic()
    except Exception as e:
        if os.getenv('ENVIRONMENT') == 'production':
            raise RuntimeError(f"Failed to configure Logfire in production: {e}")
        print(f"Warning: Failed to configure Logfire: {e}. Running without logging in development mode.")

class timed_lru_cache:
    """
    Decorator that adds time-based expiration to LRU cache
    """

    def __init__(self, maxsize: int = 128, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Any] = {}
        self.last_refresh: Dict[str, float] = {}

    def __call__(
            self, func: Callable[...,
                                 Awaitable[T]]) -> Callable[..., Awaitable[T]]:

        @wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> T:
            key = str((args, sorted(kwargs.items())))

            # Check if cache needs refresh
            now = time.time()
            if (key not in self.cache
                    or now - self.last_refresh.get(key, 0) > self.ttl_seconds):
                self.cache[key] = await func(*args, **kwargs)
                self.last_refresh[key] = now

                # Implement LRU by removing oldest items if cache is too large
                if len(self.cache) > self.maxsize:
                    # Find the key with the oldest timestamp
                    oldest_key = None
                    oldest_time = float('inf')

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
    CONTENT_TYPE_MAP = {
        'bookmarks': Bookmark,
        'til': TIL,
        'notes': Note,
        'how_to': Note,  # Using Note model for how-to guides
        'pages': Note,   # Using Note model for pages
    }

    @staticmethod
    def render_markdown(file_path: str) -> dict:
        if not os.path.exists(file_path):
            return {"html": "", "metadata": {}, "errors": ["File not found"]}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML front matter and validate with Pydantic
        metadata, md_content, errors = ContentManager._parse_front_matter(content, file_path)

        # Convert and sanitize markdown
        html_content = ContentManager._convert_markdown(md_content)
        return {"html": html_content, "metadata": metadata, "errors": errors}

    @staticmethod
    def _parse_front_matter(content: str, file_path: str) -> tuple:
        errors = []
        if content.startswith('---'):
            try:
                _, fm, md_content = content.split('---', 2)
                raw_metadata = yaml.safe_load(fm)
                
                # Determine content type from file path
                path_parts = file_path.split(os.sep)
                content_type = path_parts[-2] if len(path_parts) > 1 else 'notes'
                
                # Get the appropriate model
                model_class = ContentManager.CONTENT_TYPE_MAP.get(content_type, BaseContent)
                
                try:
                    # Convert string dates to datetime objects
                    if isinstance(raw_metadata.get('created'), str):
                        raw_metadata['created'] = datetime.strptime(raw_metadata['created'], '%Y-%m-%d')
                    if isinstance(raw_metadata.get('updated'), str):
                        raw_metadata['updated'] = datetime.strptime(raw_metadata['updated'], '%Y-%m-%d')
                    
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
                md.inlinePatterns.register(InlineCodePattern(r'(?<!\\)(`+)(.+?)(?<!`)\1(?!`)', md), 'backtick', 175)
        
        class InlineCodePattern(markdown.inlinepatterns.Pattern):
            def handleMatch(self, m):
                el = markdown.util.etree.Element('span')
                el.set('class', 'inline-code')
                code = markdown.util.etree.SubElement(el, 'code')
                code.text = markdown.util.AtomicString(m.group(2))
                return el

        # Custom FencedCode extension to preserve link styling
        class CustomFencedCodeExtension(FencedCodeExtension):
            def extendMarkdown(self, md):
                """ Add FencedBlockPreprocessor to the Markdown instance. """
                md.registerExtension(self)
                config = self.getConfigs()
                processor = markdown.extensions.fenced_code.FencedBlockPreprocessor(md, config)
                processor.run = lambda lines: self.custom_run(processor, lines)  # Override the run method
                md.preprocessors.register(processor, 'fenced_code_block', 25)

            def custom_run(self, processor, lines):
                """ Custom run method to preserve link styling within code blocks """
                new_lines = []
                for line in lines:
                    if line.strip().startswith('```'):
                        new_lines.append(line)
                    else:
                        # Replace markdown links with HTML links that have our styling
                        line = re.sub(
                            r'\[(.*?)\]\((.*?)\)',
                            r'<a href="\2" class="text-emerald-600 hover:text-emerald-500 hover:underline">\1</a>',
                            line
                        )
                        new_lines.append(line)
                return processor.__class__.run(processor, new_lines)

        md = markdown.Markdown(extensions=[
            'extra',
            'admonition',
            TocExtension(baselevel=1),
            CustomFencedCodeExtension(),
            InlineCodeExtension()
        ])
        
        html_content = md.convert(content)
        
        # Use BeautifulSoup to modify link styles
        soup = BeautifulSoup(html_content, 'html.parser')
        for link in soup.find_all('a'):
            existing_classes = link.get('class', [])
            if isinstance(existing_classes, str):
                existing_classes = existing_classes.split()
            new_classes = existing_classes + ['text-emerald-600', 'hover:text-emerald-500', 'hover:underline']
            link['class'] = ' '.join(new_classes)
        
        # Update ALLOWED_ATTRIBUTES to ensure classes survive sanitization
        allowed_attrs = {
            **ALLOWED_ATTRIBUTES,
            'a': ['href', 'title', 'rel', 'class', 'target'],
            'iframe': ['src', 'width', 'height', 'frameborder', 'allow', 'allowfullscreen', 'title', 'referrerpolicy'],
        }
        
        clean_html = bleach.clean(
            str(soup),
            tags=ALLOWED_TAGS,
            attributes=allowed_attrs,
            strip=True
        )
        
        return clean_html

    @staticmethod
    def get_content(content_type: str, limit=None):
        """Get content of a specific type with consistent format"""
        files = glob.glob(f"{CONTENT_DIR}/{content_type}/*.md")
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        content = []
        validation_errors = {}
        
        for file in files:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            metadata = file_content["metadata"]
            errors = file_content.get("errors", [])

            if errors:
                validation_errors[file] = errors
                # Skip invalid content in production, include with errors in development
                if os.getenv("ENVIRONMENT") == "production":
                    continue

            # Get excerpt
            soup = BeautifulSoup(file_content["html"], 'html.parser')
            first_p = soup.find('p')
            excerpt = first_p.get_text() if first_p else ""

            # Create consistent content item structure
            content_item = {
                "name": name,
                "title": metadata.get("title", name.replace('-', ' ').title()),
                "created": metadata.get("created", ""),
                "updated": metadata.get("updated", ""),
                "metadata": metadata,
                "excerpt": excerpt,
                "url": f"/{content_type}/{name}",
                "content_type": content_type,
                "type_indicator": {
                    "notes": "Note",
                    "how_to": "How To",
                    "bookmarks": "Bookmark",
                    "til": "TIL"
                }.get(content_type, ""),
                "html": file_content["html"]
            }
            
            if errors and os.getenv("ENVIRONMENT") != "production":
                content_item["validation_errors"] = errors

            content.append(content_item)

        # Log validation errors
        if validation_errors:
            logfire.warning('content_validation_errors', 
                          content_type=content_type, 
                          errors=validation_errors)

        return {
            "content": content[:limit] if limit else content,
            "total": len(content),
            "type": content_type
        }

    @staticmethod
    def _get_date_from_filename(filename: str) -> str:
        match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(filename))
        return match.group(1) if match else '0000-00-00'

    @staticmethod
    def get_random_quote():
        quote_files = glob.glob(f"{CONTENT_DIR}/notes/*quoting*.md")
        if not quote_files:
            return None

        random_quote_file = random.choice(quote_files)
        quote_content = ContentManager.render_markdown(random_quote_file)

        # Extract quote safely
        soup = BeautifulSoup(quote_content["html"], 'html.parser')
        blockquote = soup.find('blockquote')
        quote_text = blockquote.get_text() if blockquote else ""

        return {
            "title": quote_content["metadata"].get("title", ""),
            "content": quote_text
        }

    @staticmethod
    def get_bookmarks(limit: Optional[int] = 10) -> List[dict]:
        """Get bookmarks with pagination"""
        files = glob.glob(f"{CONTENT_DIR}/bookmarks/*.md")
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)
        bookmarks = []
        files_to_process = files if limit is None else sorted(
            files, reverse=True)[:limit]

        for file in files_to_process:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            metadata = file_content["metadata"]

            # Convert the metadata to a Bookmark model for validation
            try:
                bookmark = Bookmark(**metadata)
                bookmarks.append({
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
                    "source": bookmark.source
                })
            except ValidationError as e:
                logfire.error('bookmark_validation_error', 
                            bookmark_name=name, 
                            error=str(e))
                continue

        return bookmarks

    @staticmethod
    def get_posts_by_tag(tag: str, content_types: List[str] = None):
        posts = []
        if content_types is None:
            content_types = ["notes", "how_to", "til"]

        for content_type in content_types:
            files = glob.glob(f"{CONTENT_DIR}/{content_type}/*.md")
            for file in files:
                name = os.path.splitext(os.path.basename(file))[0]
                file_content = ContentManager.render_markdown(file)
                metadata = file_content["metadata"]

                if "tags" in metadata and tag in metadata["tags"]:
                    # Get excerpt for all post types
                    soup = BeautifulSoup(file_content["html"], 'html.parser')
                    first_p = soup.find('p')
                    excerpt = first_p.get_text() if first_p else ""

                    posts.append({
                        "type":
                        content_type,
                        "name":
                        name,
                        "title":
                        metadata.get("title",
                                     name.replace('-', ' ').title()),
                        "created":
                        metadata.get("created", ""),
                        "updated":
                        metadata.get("updated", ""),
                        "metadata":
                        metadata,
                        "excerpt":
                        excerpt,
                        "url":
                        f"/{content_type}/{name}"
                    })

        return sorted(posts, key=lambda x: x.get("created", ""), reverse=True)

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
                f"https://api.github.com/users/{ai_config.github_username}/starred",
                params={
                    "page": page,
                    "per_page": per_page
                })

            # Handle rate limiting
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                reset_time = int(response.headers['X-RateLimit-Reset'])
                if remaining == 0:
                    reset_datetime = datetime.fromtimestamp(reset_time)
                    logfire.warning('github_rate_limit_exceeded', 
                                  reset_time=reset_datetime.isoformat())
                    return {
                        "stars": [],
                        "next_page": None,
                        "error": "Rate limit exceeded. Please try again later."
                    }

            if response.status_code != 200:
                logfire.error('github_api_error', 
                            status_code=response.status_code, 
                            response_text=response.text)
                return {
                    "stars": [],
                    "next_page": None,
                    "error": f"GitHub API error: {response.status_code}"
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
                stars.append({
                    "name":
                    repo["name"],
                    "full_name":
                    repo["full_name"],
                    "description":
                    repo["description"],
                    "url":
                    repo["html_url"],
                    "language":
                    repo["language"],
                    "stars":
                    repo["stargazers_count"],
                    "starred_at":
                    datetime.strptime(
                        repo["updated_at"],
                        "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
                })

            return {"stars": stars, "next_page": next_page, "error": None}

        except httpx.RequestError as e:
            logfire.error('github_request_error', error=str(e))
            return {
                "stars": [],
                "next_page": None,
                "error": "Failed to fetch GitHub stars"
            }

    @staticmethod
    def ttl_hash(seconds=3600):
        """Return the same value within `seconds` time period"""
        return round(datetime.now().timestamp() / seconds)

    @staticmethod
    def get_til_posts(page: int = 1, per_page: int = 30) -> dict:
        """Get TiL posts with pagination"""
        files = glob.glob(f"{CONTENT_DIR}/til/*.md")
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_files = files[start_idx:end_idx]

        tils = []
        til_tags = {}

        for file in page_files:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            metadata = file_content["metadata"]

            # Get first paragraph for excerpt
            soup = BeautifulSoup(file_content["html"], 'html.parser')
            first_p = soup.find('p')
            excerpt = first_p.get_text() if first_p else ""

            # Update tag counts
            for tag in metadata.get("tags", []):
                til_tags[tag] = til_tags.get(tag, 0) + 1

            tils.append({
                "name":
                name,
                "title":
                metadata.get("title",
                             name.replace('-', ' ').title()),
                "created":
                metadata.get("created", ""),
                "updated":
                metadata.get("updated", ""),
                "tags":
                metadata.get("tags", []),
                "excerpt":
                excerpt,
                "url":
                f"/til/{name}"
            })

        return {
            "tils": tils,
            "til_tags": til_tags,
            "next_page": page + 1 if end_idx < len(files) else None
        }

    @staticmethod
    def get_til_posts_by_tag(tag: str) -> List[dict]:
        """Get TiL posts filtered by tag"""
        files = glob.glob(f"{CONTENT_DIR}/til/*.md")
        tils = []

        for file in files:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            metadata = file_content["metadata"]

            if tag in metadata.get("tags", []):
                soup = BeautifulSoup(file_content["html"], 'html.parser')
                first_p = soup.find('p')
                excerpt = first_p.get_text() if first_p else ""

                tils.append({
                    "name":
                    name,
                    "title":
                    metadata.get("title",
                                 name.replace('-', ' ').title()),
                    "created":
                    metadata.get("created", ""),
                    "updated":
                    metadata.get("updated", ""),
                    "tags":
                    metadata.get("tags", []),
                    "excerpt":
                    excerpt,
                    "url":
                    f"/til/{name}"
                })

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
                        if "metadata" not in item and content_type in ["bookmarks", "til"]:
                            item["metadata"] = {
                                "title": item.get("title", ""),
                                "created": item.get("created", ""),
                                "updated": item.get("updated", ""),
                                "tags": item.get("tags", [])
                            }
                        
                        # Generate excerpt if not present
                        if "excerpt" not in item and "html" in item:
                            soup = BeautifulSoup(item["html"], 'html.parser')
                            first_p = soup.find('p')
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
                            "til": "TIL"
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
                    "errors": errors
                }
            
            has_more = end_idx < len(all_content)
            
            return {
                "content": all_content[start_idx:end_idx],
                "next_page": page + 1 if has_more else None,
                "total": len(all_content),
                "current_page": page,
                "total_pages": (len(all_content) + per_page - 1) // per_page,
                "errors": errors
            }
            
        except Exception as e:
            raise ValueError(f"Error retrieving mixed content: {str(e)}")


def generate_rss_feed():
    # Get all content
    notes = ContentManager.get_content("notes")
    how_tos = ContentManager.get_content("how_to")
    til_result = ContentManager.get_til_posts(page=1, per_page=9999)
    tils = til_result["tils"]

    # Combine all content
    all_content = []
    all_content.extend([(item, "notes") for item in notes])
    all_content.extend([(item, "how_to") for item in how_tos])
    all_content.extend([(item, "til") for item in tils])

    def get_created_date(x):
        item = x[0]
        return item.get("created", "") if "created" in item else item.get("metadata", {}).get("created", "")

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
        rss += '<item>\n'
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
            rss += f'<pubDate>{format_datetime(date)}</pubDate>\n'

        # Add categories/tags
        if content_type in ["notes", "how_to"]:
            tags = item.get("metadata", {}).get("tags", [])
        else:  # TiL
            tags = item.get("tags", [])

        for tag in tags:
            rss += f'<category>{tag}</category>\n'

        rss += f'<guid>{content_config.base_url}/{content_type}/{item["name"]}</guid>\n'
        rss += '</item>\n'

    rss += '</channel>\n'
    rss += '</rss>'

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
        "/bookmarks"  # Keep bookmarks, remove stars
    ]
    
    for page in static_pages:
        sitemap += '  <url>\n'
        sitemap += f'    <loc>{base_url}{page}</loc>\n'
        sitemap += '    <changefreq>weekly</changefreq>\n'
        sitemap += '    <priority>0.8</priority>\n'
        sitemap += '  </url>\n'
    
    # Add notes
    notes = ContentManager.get_content("notes")
    for note in notes:
        metadata = note.get("metadata", {})
        # Only include content with appropriate status
        if metadata.get("status") in ["Evergreen", "Budding"]:
            sitemap += '  <url>\n'
            sitemap += f'    <loc>{base_url}/notes/{note["name"]}</loc>\n'
            if metadata.get("updated"):
                sitemap += f'    <lastmod>{metadata["updated"]}</lastmod>\n'
            elif metadata.get("created"):
                sitemap += f'    <lastmod>{metadata["created"]}</lastmod>\n'
            sitemap += '    <changefreq>monthly</changefreq>\n'
            sitemap += '    <priority>0.6</priority>\n'
            sitemap += '  </url>\n'
    
    # Add how-tos
    how_tos = ContentManager.get_content("how_to")
    for how_to in how_tos:
        metadata = how_to.get("metadata", {})
        # Only include content with appropriate status
        if metadata.get("status") in ["Evergreen", "Budding"]:
            sitemap += '  <url>\n'
            sitemap += f'    <loc>{base_url}/how_to/{how_to["name"]}</loc>\n'
            if metadata.get("updated"):
                sitemap += f'    <lastmod>{metadata["updated"]}</lastmod>\n'
            elif metadata.get("created"):
                sitemap += f'    <lastmod>{metadata["created"]}</lastmod>\n'
            sitemap += '    <changefreq>monthly</changefreq>\n'
            sitemap += '    <priority>0.6</priority>\n'
            sitemap += '  </url>\n'
    
    # Add TIL posts
    til_result = ContentManager.get_til_posts(page=1, per_page=9999)
    for til in til_result["tils"]:
        # Only include content with appropriate status
        if til.get("status") in ["Evergreen", "Budding"]:
            sitemap += '  <url>\n'
            sitemap += f'    <loc>{base_url}/til/{til["name"]}</loc>\n'
            if til.get("updated"):
                sitemap += f'    <lastmod>{til["updated"]}</lastmod>\n'
            elif til.get("created"):
                sitemap += f'    <lastmod>{til["created"]}</lastmod>\n'
            sitemap += '    <changefreq>monthly</changefreq>\n'
            sitemap += '    <priority>0.6</priority>\n'
            sitemap += '  </url>\n'
    
    # Add bookmarks
    bookmarks = ContentManager.get_bookmarks()
    for bookmark in bookmarks:
        sitemap += '  <url>\n'
        sitemap += f'    <loc>{base_url}/bookmarks/{bookmark["name"]}</loc>\n'
        if bookmark.get("updated"):
            sitemap += f'    <lastmod>{bookmark["updated"]}</lastmod>\n'
        elif bookmark.get("created"):
            sitemap += f'    <lastmod>{bookmark["created"]}</lastmod>\n'
        sitemap += '    <changefreq>monthly</changefreq>\n'
        sitemap += '    <priority>0.4</priority>\n'  # Lower priority for bookmarks
        sitemap += '  </url>\n'
    
    # Close sitemap
    sitemap += '</urlset>'
    return sitemap


@app.get("/feed.xml")
@app.get("/feed")
async def rss_feed():
    rss_content = generate_rss_feed()
    return Response(content=rss_content, media_type="application/xml")


@app.get("/sitemap.xml")
async def sitemap():
    """Serve the XML sitemap"""
    sitemap_content = generate_sitemap()
    return Response(
        content=sitemap_content,
        media_type="application/xml"
    )


@app.get("/robots.txt")
async def robots():
    return Response(
        content=f"""User-agent: *
Allow: /
Sitemap: {content_config.base_url}/sitemap.xml""",
        media_type="text/plain"
    )


# Route handlers
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    template = env.get_template("index.html")
    home_content = ContentManager.render_markdown(
        f"{CONTENT_DIR}/pages/home.md")

    # Get mixed content for the home page
    mixed_content = await ContentManager.get_mixed_content(page=1, per_page=10)

    # Fetch GitHub stars asynchronously
    stars_result = await ContentManager.get_github_stars(page=1, per_page=5)

    return HTMLResponse(
        content=template.render(
            request=request,
            content=home_content["html"],
            metadata=home_content["metadata"],
            mixed_content=mixed_content["content"],
            has_more=mixed_content["next_page"] is not None,
            random_quote=ContentManager.get_random_quote(),
            github_stars=stars_result["stars"],
            github_error=stars_result["error"]
        )
    )


@app.get("/now", response_class=HTMLResponse)
async def read_now(request: Request):
    template = env.get_template("content_page.html")
    now_content = ContentManager.render_markdown(f"{CONTENT_DIR}/pages/now.md")
    return HTMLResponse(content=template.render(
        request=request,
        content=now_content["html"],
        metadata=now_content["metadata"],
        recent_how_tos=ContentManager.get_content("how_to", limit=5),
        recent_notes=ContentManager.get_content("notes", limit=5)))


@app.get("/tags/{tag}", response_class=HTMLResponse)
async def read_tag(request: Request, tag: str):
    # Get content type from query parameter, default to all
    content_type = request.query_params.get("type")
    content_types = [content_type] if content_type else None

    posts = ContentManager.get_posts_by_tag(tag, content_types=content_types)
    template_name = "partials/tags.html" if request.headers.get(
        "HX-Request") == "true" else "tags.html"

    return HTMLResponse(content=env.get_template(template_name).render(
        request=request, tag=tag, posts=posts, content_type=content_type))


@app.get("/api/mixed-content", response_class=HTMLResponse)
async def get_mixed_content_api(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    content_types: Optional[List[str]] = None
):
    """API endpoint for retrieving mixed content with pagination"""
    with logfire.span('mixed_content_api', page=page, per_page=per_page):
        try:
            if page < 1:
                raise HTTPException(status_code=400, detail="Page number must be greater than 0")
            if per_page < 1:
                raise HTTPException(status_code=400, detail="Items per page must be greater than 0")
            if per_page > 100:
                raise HTTPException(status_code=400, detail="Items per page cannot exceed 100")
                
            with logfire.span('fetching_mixed_content'):
                result = await ContentManager.get_mixed_content(page=page, per_page=per_page)
                logfire.debug('mixed_content_result', 
                            next_page=result['next_page'], 
                            content_length=len(result['content']),
                            total=result['total'])
            
            with logfire.span('rendering_template'):
                template = env.get_template("partials/mixed_content_page.html")
                html_content = template.render(
                    content=result["content"],
                    next_page=result["next_page"]
                )
                logfire.debug('template_rendered', html_length=len(html_content))
            
            return HTMLResponse(content=html_content)
            
        except ValueError as e:
            logfire.error('value_error', error=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logfire.error('unexpected_error', error=str(e))
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/{content_type}/{page_name}", response_class=HTMLResponse)
async def read_content(request: Request, content_type: str, page_name: str):
    file_path = f"{CONTENT_DIR}/{content_type}/{page_name}.md"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Content not found")

    content_data = ContentManager.render_markdown(file_path)
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = "partials/content.html" if is_htmx else "content_page.html"

    logfire.debug('rendering_content', 
                 template=template_name, 
                 is_htmx=is_htmx, 
                 content_type=content_type,
                 page_name=page_name)

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            content=content_data["html"],
            metadata=content_data["metadata"],
            content_type=content_type,
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5)
        )
    )


@app.get("/bookmarks", response_class=HTMLResponse)
async def read_bookmarks(request: Request):
    template_name = "partials/bookmarks.html" if request.headers.get(
        "HX-Request") == "true" else "bookmarks.html"
    return HTMLResponse(content=env.get_template(template_name).render(
        request=request,
        bookmarks=ContentManager.get_bookmarks(
            limit=9999),  # Using a large number instead of None
        recent_how_tos=ContentManager.get_content("how_to", limit=5),
        recent_notes=ContentManager.get_content("notes", limit=5)))


@app.get("/stars", response_class=HTMLResponse)
async def read_stars(request: Request):
    template_name = "partials/stars.html" if request.headers.get(
        "HX-Request") == "true" else "stars.html"
    result = await ContentManager.get_github_stars(page=1)
    return HTMLResponse(content=env.get_template(template_name).render(
        request=request,
        github_stars=result["stars"],
        next_page=result["next_page"],
        error=result["error"],
        recent_how_tos=ContentManager.get_content("how_to", limit=5),
        recent_notes=ContentManager.get_content("notes", limit=5)))


@app.get("/stars/page/{page}", response_class=HTMLResponse)
async def read_stars_page(request: Request, page: int):
    result = await ContentManager.get_github_stars(page=page)

    # If there's an error, return it with appropriate styling
    if result["error"]:
        return HTMLResponse(
            content=
            f'<div class="p-4 bg-red-100 text-red-700 rounded">{result["error"]}</div>',
            headers={
                "HX-Retarget": "#loading-indicator",
                "HX-Reswap": "outerHTML"
            })

    return HTMLResponse(content=env.get_template(
        "partials/stars_page.html").render(request=request,
                                           github_stars=result["stars"],
                                           next_page=result["next_page"]))


@app.get("/til", response_class=HTMLResponse)
async def read_til(request: Request):
    template_name = "partials/til.html" if request.headers.get(
        "HX-Request") == "true" else "til.html"
    result = ContentManager.get_til_posts(page=1)

    return HTMLResponse(content=env.get_template(template_name).render(
        request=request,
        tils=result["tils"],
        til_tags=result["til_tags"],
        next_page=result["next_page"],
        recent_how_tos=ContentManager.get_content("how_to", limit=5),
        recent_notes=ContentManager.get_content("notes", limit=5)))


@app.get("/til/tag/{tag}", response_class=HTMLResponse)
async def read_til_tag(request: Request, tag: str):
    template_name = "partials/til.html" if request.headers.get(
        "HX-Request") == "true" else "til.html"
    tils = ContentManager.get_til_posts_by_tag(tag)

    # Get all tags for the sidebar
    all_tils = ContentManager.get_til_posts(page=1)

    return HTMLResponse(content=env.get_template(template_name).render(
        request=request,
        tils=tils,
        til_tags=all_tils["til_tags"],
        next_page=None,  # No pagination for tag views
        recent_how_tos=ContentManager.get_content("how_to", limit=5),
        recent_notes=ContentManager.get_content("notes", limit=5)))


@app.get("/til/page/{page}", response_class=HTMLResponse)
async def read_til_page(request: Request, page: int):
    result = ContentManager.get_til_posts(page=page)

    return HTMLResponse(content=env.get_template(
        "partials/til_page.html").render(request=request,
                                         tils=result["tils"],
                                         next_page=result["next_page"]))


@app.get("/til/{til_name}", response_class=HTMLResponse)
async def read_til_post(request: Request, til_name: str):
    file_path = f"{CONTENT_DIR}/til/{til_name}.md"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="TIL post not found")

    content_data = ContentManager.render_markdown(file_path)
    template_name = "content_page.html"

    return HTMLResponse(content=env.get_template(template_name).render(
        request=request,
        content=content_data["html"],
        metadata=content_data["metadata"],
        recent_how_tos=ContentManager.get_content("how_to", limit=5),
        recent_notes=ContentManager.get_content("notes", limit=5)))


@app.get("/projects", response_class=HTMLResponse)
async def read_projects(request: Request):
    template = env.get_template("content_page.html")
    projects_content = ContentManager.render_markdown(f"{CONTENT_DIR}/pages/projects.md")
    return HTMLResponse(content=template.render(
        request=request,
        content=projects_content["html"],
        metadata=projects_content["metadata"],
        recent_how_tos=ContentManager.get_content("how_to", limit=5),
        recent_notes=ContentManager.get_content("notes", limit=5)))


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring application status"""
    try:
        # Basic application health check
        return JSONResponse(
            content={
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": os.getenv("APP_VERSION", "1.0.0"),
                "environment": os.getenv("ENVIRONMENT", "production")
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )
