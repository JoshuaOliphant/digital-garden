# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
import markdown
import os
import yaml
import glob
import logging
import subprocess

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader("app/templates"))

# Custom Markdown extension to add HTMX attributes to links
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

class HTMXLinkProcessor(Treeprocessor):
    def run(self, root):
        for element in root.iter('a'):
            href = element.get('href', '')
            if href.startswith('/pages/'):
                element.set('hx-get', href)
                element.set('hx-target', '#content-area')
                element.set('hx-swap', 'innerHTML')
                existing_class = element.get('class', '')
                element.set('class', f"{existing_class} text-blue-500 hover:underline".strip())

class HTMXLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(HTMXLinkProcessor(md), 'htmx_link', 15)

def render_markdown(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith('---'):
        _, fm, md_content = content.split('---', 2)
        metadata = yaml.safe_load(fm)
    else:
        metadata = {}
        md_content = content
    html_content = markdown.markdown(
        md_content,
        extensions=["extra", "toc", HTMXLinkExtension()]
    )
    return {"html": html_content, "metadata": metadata}

def get_all_pages():
    md_files = glob.glob("app/pages/*.md")
    pages = [os.path.splitext(os.path.basename(f))[0] for f in md_files]
    return pages

def get_change_history(page_name):
    file_path = f"app/pages/{page_name}.md"
    try:
        # Get the last 5 commits for the file
        logs = subprocess.check_output(
            ["git", "log", "--pretty=format:%h - %s (%ad)", "--date=short", "-n", "5", file_path],
            stderr=subprocess.STDOUT
        )
        return logs.decode("utf-8").split('\n')
    except subprocess.CalledProcessError:
        return []

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logging.info("Rendering root page")
    template = env.get_template("index.html")
    content_data = render_markdown("app/pages/sample-page.md")
    pages = get_all_pages()
    all_tags = get_all_tags()
    return template.render(
        request=request,
        content=content_data["html"],
        metadata=content_data.get("metadata", {}),
        pages=pages,
        all_tags=all_tags
    )

@app.get("/pages/{page_name}", response_class=HTMLResponse)
async def read_page(request: Request, page_name: str):
    logging.info(f"Rendering page: {page_name}")
    file_path = f"app/pages/{page_name}.md"
    if not os.path.exists(file_path):
        logging.warning(f"Page not found: {page_name}")
        return HTMLResponse(content="Page not found.", status_code=404)
    content_data = render_markdown(file_path)
    change_history = get_change_history(page_name)
    return HTMLResponse(
        content=env.get_template("partials/content.html").render(
            content=content_data["html"],
            metadata=content_data.get("metadata", {}),
            change_history=change_history
        )
    )

@app.get("/modal-content", response_class=HTMLResponse)
async def modal_content(request: Request):
    return env.get_template("partials/modal_content.html").render()

def get_all_tags():
    md_files = glob.glob("app/pages/*.md")
    tags = set()
    for file in md_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith('---'):
                _, fm, _ = content.split('---', 2)
                metadata = yaml.safe_load(fm)
                tags.update(metadata.get('tags', []))
    return sorted(tags)
