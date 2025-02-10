# Details Needed for Content Migration

## 1. Content Structure

### Location of Content Files
- Main content directory: `app/content/`
- Content is organized into several subdirectories based on content type

### Content Types
1. Bookmarks (`app/content/bookmarks/`)
2. How-to guides (`app/content/how_to/`)
3. Notes (`app/content/notes/`)
4. TIL (Today I Learned) (`app/content/til/`)
5. Pages (`app/content/pages/`)

### Front Matter Structure
Common front matter fields across content types include:
```yaml
---
title: "Title of the content"
status: "Evergreen"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
tags: [tag1, tag2, tag3]
---
```

Additional fields by content type:
- Bookmarks: includes `url` field
- Other types may have specific fields based on content needs

## 2. Current Content Organization

### Directory Structure
```
app/content/
├── bookmarks/
├── how_to/
├── notes/
├── pages/
└── til/
```

### File Naming Conventions
- Files follow the pattern: `YYYY-MM-DD-title-slug.md`
- Example: `2024-03-14-unix-philosophy-for-ai.md`
- All content files are Markdown (.md) format

### Content Relationships
- Content is primarily organized by tags
- Tags are used to create relationships between different content types
- No explicit series structure identified, but content can be related through common tags

## 3. Content Processing

### Processing System
- Uses FastAPI for serving content
- Main processing file: `app/main.py`
- Content processing handled by `ContentManager` class in `main.py`

### Key Processing Features
- Markdown rendering with extensions (TOC, Fenced Code)
- Front matter parsing using YAML
- HTML sanitization using Bleach
- RSS feed generation
- Sitemap generation
- Tag-based content filtering
- Pagination support for TIL posts

### Validation
- Basic front matter validation through YAML parsing
- HTML sanitization for security
- No explicit validation scripts identified

## 4. Dependencies

### Python Version
- Requires Python >= 3.12

### Key Dependencies
```toml
dependencies = [
    "beautifulsoup4>=4.12.3",
    "bleach>=6.1.0",
    "cairosvg>=2.7.1",
    "fastapi>=0.115.0",
    "httpx>=0.27.2",
    "jinja2>=3.1.4",
    "markdown>=3.7",
    "openai>=1.50.0",
    "pydantic>=2.9.2",
    "pyyaml>=6.0.2",
    "uvicorn>=0.30.6"
]
```

### Package Management
- Uses `pyproject.toml` and `uv` for dependency management
- Modern Python packaging standards with explicit version requirements
