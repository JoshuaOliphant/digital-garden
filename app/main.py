from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
import markdown
from markdown.treeprocessors import Treeprocessor
import os
import yaml
import glob
import bleach
import random
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from bs4 import BeautifulSoup

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 templates
env = Environment(loader=FileSystemLoader("app/templates"))

# Define allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "ul", "ol", "li", "strong", "em", "a", "img",
    "table", "thead", "tbody", "tr", "th", "td"
]
ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
}

def render_markdown(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {"html": "", "metadata": {}}

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse YAML front matter if present
    if content.startswith('---'):
        try:
            _, fm, md_content = content.split('---', 2)
            metadata = yaml.safe_load(fm)
        except ValueError:
            metadata = {}
            md_content = content
    else:
        metadata = {}
        md_content = content

    # Initialize Markdown with desired extensions
    md = markdown.Markdown(extensions=[
        'extra',
        'admonition',
        TocExtension(baselevel=1),
        FencedCodeExtension(),
    ])

    # Convert Markdown to HTML
    html_content = md.convert(md_content)

    # Sanitize the HTML to prevent XSS
    clean_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    # Optionally, linkify URLs that were not turned into links
    clean_html = bleach.linkify(clean_html)

    return {"html": clean_html, "metadata": metadata}

def get_content(content_type: str, limit=None):
    files = glob.glob(f"app/content/{content_type}/*.md")
    content = []
    for file in files:
        name = os.path.splitext(os.path.basename(file))[0]
        file_content = render_markdown(file)
        content.append({
            "name": name,
            "title": file_content["metadata"].get("title", name.replace('-', ' ').title()),
            "metadata": file_content["metadata"]
        })
    if limit:
        return content[:limit]
    return content

@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    template = env.get_template("index.html")
    home_content = render_markdown("app/content/pages/home.md")
    how_tos = get_content("how_to")
    notes = get_content("notes")
    random_quote = get_random_quote()
    recent_bookmarks = get_bookmarks(limit=10)
    return HTMLResponse(
        content=template.render(
            request=request,
            content=home_content["html"],
            metadata=home_content["metadata"],
            how_tos=how_tos,
            notes=notes,
            random_quote=random_quote,
            recent_bookmarks=recent_bookmarks
        )
    )

@app.get("/now", response_class=HTMLResponse)
async def read_now(request: Request):
    template = env.get_template("content_page.html")
    now_content = render_markdown("app/content/pages/now.md")
    recent_how_tos = get_content("how_to", limit=5)
    recent_notes = get_content("notes", limit=5)
    return HTMLResponse(
        content=template.render(
            request=request,
            content=now_content["html"],
            metadata=now_content["metadata"],
            recent_how_tos=recent_how_tos,
            recent_notes=recent_notes
        )
    )

@app.get("/{content_type}/{page_name}", response_class=HTMLResponse)
async def read_content(request: Request, content_type: str, page_name: str):
    file_path = f"app/content/{content_type}/{page_name}.md"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Content not found")

    content_data = render_markdown(file_path)
    recent_how_tos = get_content("how_to", limit=5)
    recent_notes = get_content("notes", limit=5)

    if request.headers.get("HX-Request") == "true":
        # This is an HTMX request, return only the content partial
        return HTMLResponse(
            content=env.get_template("partials/content.html").render(
                content=content_data["html"],
                metadata=content_data["metadata"],
                recent_how_tos=recent_how_tos,
                recent_notes=recent_notes
            )
        )
    else:
        # This is a full page request, return the complete page
        return HTMLResponse(
            content=env.get_template("content_page.html").render(
                request=request,
                content=content_data["html"],
                metadata=content_data["metadata"],
                recent_how_tos=recent_how_tos,
                recent_notes=recent_notes
            )
        )

def get_random_quote():
    quote_files = glob.glob("app/content/notes/*quoting*.md")
    if not quote_files:
        return None

    random_quote_file = random.choice(quote_files)
    quote_content = render_markdown(random_quote_file)

    # Extract the blockquote from the content
    soup = BeautifulSoup(quote_content["html"], 'html.parser')
    blockquote = soup.find('blockquote')
    quote_text = blockquote.decode_contents() if blockquote else ""

    return {
        "title": quote_content["metadata"].get("title", ""),
        "content": quote_text
    }

def get_bookmarks(limit=10):
    files = glob.glob("app/content/bookmarks/*.md")
    bookmarks = []
    for file in sorted(files, reverse=True)[:limit]:
        name = os.path.splitext(os.path.basename(file))[0]
        file_content = render_markdown(file)
        bookmarks.append({
            "name": name,
            "title": file_content["metadata"].get("title", name.replace('-', ' ').title()),
            "url": file_content["metadata"].get("url", ""),
            "date": name[:10]  # Extract date from filename
        })
    return bookmarks
