# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start development server with hot reload
uvicorn app.main:app --reload --port 8000

# Start with CSS watching (in separate terminal)
npm run watch:css
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_main.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test function
pytest tests/test_main.py::test_get_mixed_content_pagination
```

### Code Quality
```bash
# Format code
black .

# Type checking
mypy app/

# Lint with ruff (if installed)
ruff check .
```

### CSS Development
```bash
# Watch and rebuild CSS during development
npm run watch:css

# Build minified CSS for production
npm run build:css
```

### Content Management Scripts
```bash
# Analyze content quality with AI
python scripts/analyze_content.py

# Generate metadata for new content
python scripts/generate_metadata.py

# Enhance existing metadata
python scripts/enhance_metadata.py

# Validate YAML frontmatter
python scripts/validate_frontmatter.py
```

### Deployment
```bash
# Deploy to Fly.io
fly deploy

# Check deployment status
fly status

# View logs
fly logs
```

## Architecture Overview

### Core Application Structure

**ContentManager** (`app/main.py:84-1214`) is the central hub that:
- Parses markdown files with YAML frontmatter using `parse_markdown_with_frontmatter()`
- Implements time-based LRU caching with `timed_lru_cache` decorator for performance
- Provides mixed content aggregation combining all content types
- Handles pagination with proper boundary checking
- Integrates GitHub stars via API for project bookmarks
- Generates RSS feeds and sitemaps for SEO

### Content Processing Pipeline

1. **Content Discovery**: Files are read from `app/content/{type}/` directories
2. **Validation**: YAML frontmatter is validated against Pydantic models (`app/models.py`)
3. **Markdown Processing**: Content is converted to HTML with:
   - Custom link styling for external URLs
   - HTML sanitization with allowed tags/attributes
   - Code syntax highlighting support
4. **Template Rendering**: Jinja2 templates in `app/templates/` with HTMX partials
5. **Caching**: Processed content cached for 5 minutes to reduce I/O

### Data Models (`app/models.py`)

- **BaseContent**: Core fields shared by all content types (title, dates, tags, status)
- **Bookmark**: External links with URL validation and GitHub star tracking
- **TIL**: Quick learning snippets with optional difficulty levels
- **Note**: Long-form articles supporting series and relationships

### AI Enhancement Features

The application integrates Claude API for intelligent content processing:
- **Content Analysis** (`scripts/analyze_content.py`): Readability metrics, clustering, SEO suggestions
- **Metadata Generation**: Automatic tag suggestions and summaries
- **Quality Validation**: Writing style consistency and link checking

### Frontend Stack

- **Tailwind CSS**: Utility-first styling with custom configuration
- **HTMX**: Dynamic content loading without JavaScript frameworks
- **Jinja2 Templates**: Server-side rendering with partial templates
- **Typography Plugin**: Enhanced markdown rendering styles

### Testing Strategy

Tests use pytest with async support:
- Model validation tests ensure data integrity
- API endpoint tests verify routing and responses  
- Pagination tests check boundary conditions
- Content structure tests validate output format

## Content Structure

```
app/content/
├── bookmarks/     # External links (*.md with url field)
├── how_to/        # Step-by-step guides
├── notes/         # Articles and documentation
├── pages/         # Static pages (about, now, projects)
├── til/           # Today I Learned snippets
└── unpublished/   # Draft content (status: draft)
```

### Frontmatter Schema

```yaml
---
title: "Required title"
created: "2024-03-14"          # ISO date format
updated: "2024-03-15"          # Optional
tags: [python, fastapi]        # List of tags
status: "Evergreen"            # Evergreen|Budding|draft
difficulty: "Intermediate"     # Optional: Beginner|Intermediate|Advanced
series: "Building Apps"        # Optional: group related content
related:                       # Optional: related content links
  - notes/other-note.md
---
```

## Key Implementation Details

### Caching Strategy
- `timed_lru_cache` decorator (`app/main.py:31`) implements time-based expiration
- Default 300-second (5 minute) cache duration
- Cache key includes function arguments for proper invalidation

### HTMX Integration
- Partial templates in `app/templates/partials/` for dynamic updates
- Infinite scroll via `hx-get` and `hx-trigger="revealed"`
- Content cards load individually for better perceived performance

### GitHub Integration
- Stars fetched via GitHub API for project bookmarks
- Cached to avoid rate limiting
- Graceful fallback on API errors

### Error Handling
- Custom 404 pages for missing content
- Graceful degradation when AI services unavailable
- Comprehensive logging with Logfire integration
- --
description: Information about using uv
globs: 
---
### uv Field Manual (Code‑Gen Ready, Bootstrap‑free)

*Assumption: `uv` is already installed and available on `PATH`.*

---

## 0 — Sanity Check

```bash
uv --version               # verify installation; exits 0
```

If the command fails, halt and report to the user.

---

## 1 — Daily Workflows

### 1.1 Project ("cargo‑style") Flow

```bash
uv init myproj                     # ① create pyproject.toml + .venv
cd myproj
uv add ruff pytest httpx           # ② fast resolver + lock update
uv run pytest -q                   # ③ run tests in project venv
uv lock                            # ④ refresh uv.lock (if needed)
uv sync --locked                   # ⑤ reproducible install (CI‑safe)
```

### 1.2 Script‑Centric Flow (PEP 723)

```bash
echo 'print("hi")' > hello.py
uv run hello.py                    # zero‑dep script, auto‑env
uv add --script hello.py rich      # embeds dep metadata
uv run --with rich hello.py        # transient deps, no state
```

### 1.3 CLI Tools (pipx Replacement)

```bash
uvx ruff check .                   # ephemeral run
uv tool install ruff               # user‑wide persistent install
uv tool list                       # audit installed CLIs
uv tool update --all               # keep them fresh
```

### 1.4 Python Version Management

```bash
uv python install 3.10 3.11 3.12
uv python pin 3.12                 # writes .python-version
uv run --python 3.10 script.py
```

### 1.5 Legacy Pip Interface

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip sync   -r requirements.txt   # deterministic install
```

---

## 2 — Performance‑Tuning Knobs

| Env Var                   | Purpose                 | Typical Value |
| ------------------------- | ----------------------- | ------------- |
| `UV_CONCURRENT_DOWNLOADS` | saturate fat pipes      | `16` or `32`  |
| `UV_CONCURRENT_INSTALLS`  | parallel wheel installs | `CPU_CORES`   |
| `UV_OFFLINE`              | enforce cache‑only mode | `1`           |
| `UV_INDEX_URL`            | internal mirror         | `https://…`   |
| `UV_PYTHON`               | pin interpreter in CI   | `3.11`        |
| `UV_NO_COLOR`             | disable ANSI coloring   | `1`           |

Other handy commands:

```bash
uv cache dir && uv cache info      # show path + stats
uv cache clean                     # wipe wheels & sources
```

---

## 3 — CI/CD Recipes

### 3.1 GitHub Actions

```yaml
# .github/workflows/test.yml
name: tests
on: [push]
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5       # installs uv, restores cache
      - run: uv python install            # obey .python-version
      - run: uv sync --locked             # restore env
      - run: uv run pytest -q
```

### 3.2 Docker

```dockerfile
FROM ghcr.io/astral-sh/uv:0.7.4 AS uv
FROM python:3.12-slim

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /app/
WORKDIR /app
RUN uv sync --production --locked
COPY . /app
CMD ["uv", "run", "python", "-m", "myapp"]
```

---

## 4 — Migration Matrix

| Legacy Tool / Concept | One‑Shot Replacement        | Notes                 |
| --------------------- | --------------------------- | --------------------- |
| `python -m venv`      | `uv venv`                   | 10× faster create     |
| `pip install`         | `uv pip install`            | same flags            |
| `pip-tools compile`   | `uv pip compile` (implicit) | via `uv lock`         |
| `pipx run`            | `uvx` / `uv tool run`       | no global Python req. |
| `poetry add`          | `uv add`                    | pyproject native      |
| `pyenv install`       | `uv python install`         | cached tarballs       |

---

## 5 — Troubleshooting Fast‑Path

| Symptom                    | Resolution                                                     |
| -------------------------- | -------------------------------------------------------------- |
| `Python X.Y not found`     | `uv python install X.Y` or set `UV_PYTHON`                     |
| Proxy throttling downloads | `UV_HTTP_TIMEOUT=120 UV_INDEX_URL=https://mirror.local/simple` |
| C‑extension build errors   | `unset UV_NO_BUILD_ISOLATION`                                  |
| Need fresh env             | `uv cache clean && rm -rf .venv && uv sync`                    |
| Still stuck?               | `RUST_LOG=debug uv ...` and open a GitHub issue                |

---

## 6 — Exec Pitch (30 s)

```text
• 10–100× faster dependency & env management in one binary.
• Universal lockfile ⇒ identical builds on macOS / Linux / Windows / ARM / x86.
• Backed by the Ruff team; shipping new releases ~monthly.
```

---

## 7 — Agent Cheat‑Sheet (Copy/Paste)

```bash
# new project
a=$PWD && uv init myproj && cd myproj && uv add requests rich

# test run
uv run python -m myproj ...

# lock + CI restore
uv lock && uv sync --locked

# adhoc script
uv add --script tool.py httpx
uv run tool.py

# manage CLI tools
uvx ruff check .
uv tool install pre-commit

# Python versions
uv python install 3.12
uv python pin 3.12
```

---

*End of manual*