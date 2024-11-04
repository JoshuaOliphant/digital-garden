from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from bs4 import BeautifulSoup
import markdown
import os
import re
import yaml
import glob
import bleach
import random

# Constants
CONTENT_DIR = "app/content"
TEMPLATE_DIR = "app/templates"
STATIC_DIR = "app/static"

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
    "ul", "ol", "li", "strong", "em", "a", "img", "table", "thead", "tbody",
    "tr", "th", "td"
]

ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
}

# Initialize FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

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
        clean_html = bleach.clean(
            html_content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        return bleach.linkify(clean_html)

    @staticmethod
    def get_content(content_type: str, limit=None):
        files = glob.glob(f"{CONTENT_DIR}/{content_type}/*.md")
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        content = []
        for file in files:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            content.append({
                "name": name,
                "title": file_content["metadata"].get("title", name.replace('-', ' ').title()),
                "metadata": file_content["metadata"]
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
    def get_bookmarks(limit=10):
        files = glob.glob(f"{CONTENT_DIR}/bookmarks/*.md")
        bookmarks = []
        for file in sorted(files, reverse=True)[:limit]:
            name = os.path.splitext(os.path.basename(file))[0]
            file_content = ContentManager.render_markdown(file)
            bookmarks.append({
                "name": name,
                "title": file_content["metadata"].get("title", name.replace('-', ' ').title()),
                "url": file_content["metadata"].get("url", ""),
                "date": name[:10]
            })
        return bookmarks

    @staticmethod
    def get_posts_by_tag(tag: str):
        posts = []
        content_types = ["notes", "how_to"]  # Add other content types if needed

        for content_type in content_types:
            files = glob.glob(f"{CONTENT_DIR}/{content_type}/*.md")
            for file in files:
                name = os.path.splitext(os.path.basename(file))[0]
                file_content = ContentManager.render_markdown(file)

                if "tags" in file_content["metadata"] and tag in file_content["metadata"]["tags"]:
                    posts.append({
                        "type": content_type,
                        "name": name,
                        "title": file_content["metadata"].get("title", name.replace('-', ' ').title()),
                        "metadata": file_content["metadata"]
                    })

        return sorted(posts, key=lambda x: x["name"], reverse=True)

# Route handlers
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    template = env.get_template("index.html")
    home_content = ContentManager.render_markdown(f"{CONTENT_DIR}/pages/home.md")
    return HTMLResponse(
        content=template.render(
            request=request,
            content=home_content["html"],
            metadata=home_content["metadata"],
            how_tos=ContentManager.get_content("how_to"),
            notes=ContentManager.get_content("notes"),
            random_quote=ContentManager.get_random_quote(),
            recent_bookmarks=ContentManager.get_bookmarks(limit=10)
        )
    )

@app.get("/now", response_class=HTMLResponse)
async def read_now(request: Request):
    template = env.get_template("content_page.html")
    now_content = ContentManager.render_markdown(f"{CONTENT_DIR}/pages/now.md")
    return HTMLResponse(
        content=template.render(
            request=request,
            content=now_content["html"],
            metadata=now_content["metadata"],
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5)
        )
    )

@app.get("/tags/{tag}", response_class=HTMLResponse)
async def read_tag(request: Request, tag: str):
    posts = ContentManager.get_posts_by_tag(tag)
    template_name = "partials/tags.html" if request.headers.get("HX-Request") == "true" else "tags.html"

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tag=tag,
            posts=posts
        )
    )

@app.get("/{content_type}/{page_name}", response_class=HTMLResponse)
async def read_content(request: Request, content_type: str, page_name: str):
    file_path = f"{CONTENT_DIR}/{content_type}/{page_name}.md"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Content not found")

    content_data = ContentManager.render_markdown(file_path)
    template_name = "partials/content.html" if request.headers.get("HX-Request") == "true" else "content_page.html"

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            content=content_data["html"],
            metadata=content_data["metadata"],
            recent_how_tos=ContentManager.get_content("how_to", limit=5),
            recent_notes=ContentManager.get_content("notes", limit=5)
        )
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
