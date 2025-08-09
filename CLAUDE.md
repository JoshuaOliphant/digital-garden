# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

1. Create a Python virtual environment (Python 3.12+ required):
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables:
   Create a `.env` file in the project root with:
   ```env
   # Required API keys
   ANTHROPIC_API_KEY=your_anthropic_api_key

   # Optional settings
   ENVIRONMENT=development  # or production
   CLAUDE_MODEL=claude-3-5-sonnet-latest  # or other model version
   CLAUDE_MAX_TOKENS=4096
   CLAUDE_TEMPERATURE=0.7
   ```

4. Initialize the content directories:
   ```bash
   python -c "from app.config import setup_directories; setup_directories()"
   ```

## Development Commands

1. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black .
   ```

4. Type checking:
   ```bash
   mypy .
   ```

5. Analyze content quality and structure:
   ```bash
   python scripts/analyze_content.py
   ```

## Architecture Overview

### Content Structure
The digital garden organizes content in the following directories under `app/content/`:
- `bookmarks/`: Links to interesting resources
- `how_to/`: Step-by-step guides
- `notes/`: General notes and articles
- `pages/`: Static pages (about, now, etc.)
- `til/`: Today I Learned snippets

Each content file is a Markdown file with YAML front matter containing metadata.

### Core Components
1. **ContentManager** (`app/main.py`): Central class that handles content retrieval, rendering, and organization. It provides methods for:
   - Parsing and validating markdown with YAML front matter
   - Converting markdown to HTML with proper sanitization
   - Retrieving content by type, tag, or mixed formats
   - Managing cached data with time-based expiration
   - Rendering appropriate templates for different content types

2. **Content Models** (`app/models.py`): Pydantic models that define the structure and validation rules for different content types:
   - `BaseContent`: Core fields for all content (title, dates, tags, etc.)
   - `Bookmark`: For external links and resources
   - `TIL`: For quick "Today I Learned" snippets
   - `Note`: For longer articles and how-to guides

3. **Configuration** (`app/config.py`): Manages environment variables, AI settings, and content structure configuration. Provides helpers for directory setup and config validation.

4. **Scripts**: Utility scripts for content management and enhancement:
   - `analyze_content.py`: AI-powered content quality analysis
   - `generate_metadata.py`: Auto-generate metadata for content
   - `enhance_metadata.py`: Improve existing metadata with AI
   - `validate_frontmatter.py`: Validate YAML front matter in content files

### Rendering Pipeline
1. Content files are read from disk
2. YAML front matter is parsed and validated with Pydantic models
3. Markdown is converted to HTML with custom extensions
4. HTML is sanitized with allowed tags and attributes
5. Templates are rendered with Jinja2 using the processed content and metadata

### API Routes
The FastAPI application provides routes for:
- Home page with mixed content
- Content type-specific pages (notes, bookmarks, TIL, etc.)
- Individual content pages
- Tag-based filtering
- HTMX-powered partial content loading for infinite scroll
- RSS feed and sitemap generation