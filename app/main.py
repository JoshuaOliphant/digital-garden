from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
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
from typing import List, Optional, Dict, Any, TypeVar, Callable, Awaitable
from functools import wraps
from fastapi.responses import Response
from email.utils import format_datetime

# Constants
CONTENT_DIR = "app/content"
TEMPLATE_DIR = "app/templates"
STATIC_DIR = "app/static"

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "ul",
    "ol", "li", "strong", "em", "a", "img", "table", "thead", "tbody", "tr",
    "th", "td"
]

ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
}

GITHUB_USERNAME = "JoshuaOliphant"
T = TypeVar('T')

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

    @staticmethod
    def render_markdown(file_path: str) -> dict:
        if not os.path.exists(file_path):
            return {"html": "", "metadata": {}}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML front matter
        metadata, md_content = ContentManager._parse_front_matter(content)

        # Convert and sanitize markdown
        html_content = ContentManager._convert_markdown(md_content)
        return {"html": html_content, "metadata": metadata}

    @staticmethod
    def _parse_front_matter(content: str) -> tuple:
        if content.startswith('---'):
            try:
                _, fm, md_content = content.split('---', 2)
                metadata = yaml.safe_load(fm)
                return metadata, md_content
            except ValueError:
                return {}, content
        return {}, content

    @staticmethod
    def _convert_markdown(content: str) -> str:
        md = markdown.Markdown(extensions=[
            'extra',
            'admonition',
            TocExtension(baselevel=1),
            FencedCodeExtension(),
        ])
        html_content = md.convert(content)
        clean_html = bleach.clean(html_content,
                                  tags=ALLOWED_TAGS,
                                  attributes=ALLOWED_ATTRIBUTES,
                                  strip=True)
        return bleach.linkify(clean_html)

    @staticmethod
    def get_content(content_type: str, limit=None):
        files = glob.glob(f"{CONTENT_DIR}/{content_type}/*.md")
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        content = []
        for file in files:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            metadata = file_content["metadata"]

            # Get excerpt
            soup = BeautifulSoup(file_content["html"], 'html.parser')
            first_p = soup.find('p')
            excerpt = first_p.get_text() if first_p else ""

            content.append({
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
        return content[:limit] if limit else content

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
        files = glob.glob(f"{CONTENT_DIR}/bookmarks/*.md")
        bookmarks = []
        files_to_process = files if limit is None else sorted(
            files, reverse=True)[:limit]

        for file in files_to_process:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            metadata = file_content["metadata"]

            bookmarks.append({
                "name":
                name,
                "title":
                metadata.get("title",
                             name.replace('-', ' ').title()),
                "url":
                metadata.get("url", ""),
                "created":
                metadata.get("created", ""),
                "updated":
                metadata.get("updated", ""),
                "date":
                name[:10]  # Keep this for backwards compatibility if needed
            })
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
                f"https://api.github.com/users/{GITHUB_USERNAME}/starred",
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
                    print(f"Rate limit exceeded. Resets at {reset_datetime}")
                    return {
                        "stars": [],
                        "next_page": None,
                        "error": "Rate limit exceeded. Please try again later."
                    }

            if response.status_code != 200:
                print(
                    f"GitHub API error: {response.status_code} - {response.text}"
                )
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
            print(f"Error fetching GitHub stars: {e}")
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
    rss += '<link>https://anoliphantneverforgets.com</link>\n'
    rss += '<description>Latest content from An Oliphant Never Forgets</description>\n'
    rss += '<language>en-us</language>\n'
    rss += '<managingEditor>joshua.oliphant@gmail.com (Joshua Oliphant)</managingEditor>\n'
    rss += '<webMaster>joshua.oliphant@gmail.com (Joshua Oliphant)</webMaster>\n'
    rss += '<atom:link href="https://anoliphantneverforgets.com/feed.xml" rel="self" type="application/rss+xml" />\n'

    for item, content_type in all_content:
        rss += '<item>\n'
        rss += f'<title>{item["title"]}</title>\n'
        rss += f'<link>https://anoliphantneverforgets.com/{content_type}/{item["name"]}</link>\n'
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

        rss += f'<guid>https://anoliphantneverforgets.com/{content_type}/{item["name"]}</guid>\n'
        rss += '</item>\n'

    rss += '</channel>\n'
    rss += '</rss>'

    return rss

    return rss


@app.get("/feed.xml")
@app.get("/feed")
async def rss_feed():
    rss_content = generate_rss_feed()
    return Response(content=rss_content, media_type="application/xml")


# Route handlers
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    template = env.get_template("index.html")
    home_content = ContentManager.render_markdown(
        f"{CONTENT_DIR}/pages/home.md")

    # Fetch GitHub stars asynchronously
    stars_result = await ContentManager.get_github_stars(page=1, per_page=5)

    return HTMLResponse(
        content=template.render(request=request,
                                content=home_content["html"],
                                metadata=home_content["metadata"],
                                how_tos=ContentManager.get_content("how_to"),
                                notes=ContentManager.get_content("notes"),
                                random_quote=ContentManager.get_random_quote(),
                                recent_bookmarks=ContentManager.get_bookmarks(
                                    limit=10),
                                github_stars=stars_result["stars"],
                                github_error=stars_result["error"]))


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


@app.get("/{content_type}/{page_name}", response_class=HTMLResponse)
async def read_content(request: Request, content_type: str, page_name: str):
    file_path = f"{CONTENT_DIR}/{content_type}/{page_name}.md"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Content not found")

    content_data = ContentManager.render_markdown(file_path)
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = "partials/content.html" if is_htmx else "content_page.html"

    print(f"Template used: {template_name}")  # Debug print
    print(f"Is HTMX request: {is_htmx}")     # Debug print
    print(f"Metadata: {content_data['metadata']}")  # Debug print

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
    return {"status": "healthy"}
