# PROJECT_CLAUDE.md - Digital Garden Project Configuration

This file provides comprehensive project-specific guidance for Claude Code when working with the Digital Garden application.

## Project Overview

**Type**: Python FastAPI application with uv package management  
**Frontend**: Server-side rendered with Jinja2, HTMX for interactivity, Tailwind CSS  
**Database**: File-based content storage (Markdown with YAML frontmatter)  
**Testing**: pytest with async support  
**Deployment**: Fly.io

## Technology Stack

### Backend
- **Framework**: FastAPI (async Python web framework)
- **Python**: 3.12+ with uv for package management
- **Templates**: Jinja2 with HTMX partials
- **Content**: Markdown processing with YAML frontmatter
- **Caching**: Time-based LRU cache (5-minute TTL)
- **Monitoring**: Logfire integration

### Frontend
- **CSS**: Tailwind CSS with typography plugin
- **Build**: npm scripts for CSS compilation
- **Interactivity**: HTMX for dynamic content loading
- **Icons**: Heroicons for UI elements

### AI Integration
- **API**: Anthropic Claude for content enhancement
- **Features**: Content analysis, metadata generation, quality validation

## Development Commands

### Quick Start
```bash
# Install dependencies with uv
uv sync

# Start development server with hot reload
uvicorn app.main:app --reload --port 8000

# In separate terminal: watch CSS changes
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

# Run specific test
pytest tests/test_main.py::test_get_mixed_content_pagination
```

### Code Quality
```bash
# Format code with black
black .

# Type checking
mypy app/

# Lint with ruff
ruff check .
ruff format .
```

### Content Management
```bash
# Analyze content quality
uv run python scripts/analyze_content.py

# Generate metadata
uv run python scripts/generate_metadata.py

# Enhance metadata
uv run python scripts/enhance_metadata.py

# Validate frontmatter
uv run python scripts/validate_frontmatter.py
```

### Deployment
```bash
# Deploy to Fly.io
fly deploy

# Check status
fly status

# View logs
fly logs
```

## Project Structure

```
digital_garden/
├── app/
│   ├── main.py              # FastAPI application & ContentManager
│   ├── models.py             # Pydantic models for content types
│   ├── content/              # Markdown content files
│   │   ├── bookmarks/        # External links
│   │   ├── how_to/           # Guides and tutorials
│   │   ├── notes/            # Articles and posts
│   │   ├── pages/            # Static pages
│   │   ├── til/              # Today I Learned
│   │   └── unpublished/      # Draft content
│   ├── static/
│   │   ├── css/              # Tailwind input/output
│   │   ├── js/               # JavaScript files
│   │   └── images/           # Static images
│   └── templates/
│       ├── base.html         # Base template
│       ├── index.html        # Homepage
│       └── partials/         # HTMX partials
├── tests/                    # Test suite
├── scripts/                  # Utility scripts
└── .claude/                  # Knowledge management
```

## Key Components

### ContentManager (app/main.py:84-1214)
Central hub for content management:
- Parses markdown with YAML frontmatter
- Implements caching with `timed_lru_cache`
- Provides mixed content aggregation
- Handles pagination with boundary checking
- Integrates GitHub API for stars
- Generates RSS feeds and sitemaps

### Content Models (app/models.py)
- **BaseContent**: Core fields for all content types
- **Bookmark**: External links with GitHub integration
- **TIL**: Quick learning snippets
- **Note**: Long-form articles with series support

### Template System
- Server-side rendering with Jinja2
- HTMX partials for dynamic updates
- Tailwind CSS for styling
- Typography plugin for markdown

## Development Patterns

### Content Processing Pipeline
1. Content discovery from `app/content/{type}/`
2. YAML frontmatter validation with Pydantic
3. Markdown to HTML conversion with sanitization
4. Template rendering with caching
5. HTMX partial loading for interactivity

### Caching Strategy
- Time-based LRU cache (5-minute TTL)
- Cache keys include function arguments
- Graceful degradation on cache misses

### Error Handling
- Custom 404 pages for missing content
- API fallback for external services
- Comprehensive logging with Logfire
- Validation at model level

### Testing Approach
- Async test support with pytest-asyncio
- Model validation tests
- Endpoint integration tests
- Pagination boundary tests
- Content structure validation

## Feature Flags

```python
# Environment variables for feature control
USE_COMPILED_CSS = os.getenv("USE_COMPILED_CSS", "true")
ENABLE_GARDEN_PATHS = os.getenv("ENABLE_GARDEN_PATHS", "true")
```

## Performance Considerations

### Optimization Points
- Content caching (5-minute TTL)
- Lazy loading with HTMX
- CSS minification in production
- GitHub API response caching
- Partial template rendering

### Monitoring
- Logfire integration for observability
- Error tracking and performance metrics
- API rate limit monitoring

## Security Practices

### Content Security
- HTML sanitization with bleach
- Allowed tags/attributes whitelist
- External link handling
- YAML validation with Pydantic

### API Security
- Environment variable for secrets
- Rate limiting considerations
- Graceful API failure handling

## Git Workflow

### Branch Strategy
- `main`: Production-ready code
- Feature branches for development
- Atomic commits with conventional messages

### Commit Conventions
```
feat: Add new feature
fix: Bug fix
docs: Documentation updates
style: Code formatting
refactor: Code restructuring
test: Test additions/changes
chore: Maintenance tasks
```

## Known Patterns & Solutions

### HTMX Infinite Scroll
```html
<div hx-get="/api/content?page=2" 
     hx-trigger="revealed" 
     hx-swap="afterend">
</div>
```

### Content Caching
```python
@timed_lru_cache(seconds=300)
def get_content() -> List[Content]:
    # Cached for 5 minutes
    pass
```

### Frontmatter Schema
```yaml
---
title: "Required Title"
created: "2024-03-14"
updated: "2024-03-15"
tags: [python, fastapi]
status: "Evergreen"
difficulty: "Intermediate"
---
```

## Current Focus Areas

### Active Development
- Sliding panel navigation system
- Garden paths exploration feature
- Content quality improvements
- Performance optimizations

### Technical Debt
- Test coverage expansion
- CSS compilation optimization
- Content validation enhancement
- Cache invalidation strategy

## Integration Points

### External Services
- GitHub API for project stars
- Anthropic API for AI features
- Fly.io for deployment

### Development Tools
- uv for Python dependencies
- npm for frontend tooling
- pytest for testing
- ruff for linting

## Session Management

When starting a new session:
1. Check current git status
2. Review active TODOs
3. Load project context
4. Verify test suite passes
5. Check for uncommitted changes

## Agent-Specific Overrides

### coder Agent
- Use uv for all Python operations
- Follow existing code patterns
- Maintain test coverage

### test-writer Agent
- Write tests before implementation
- Use pytest-asyncio for async tests
- Follow existing test patterns

### planner Agent
- Consider HTMX for UI changes
- Account for caching implications
- Plan for graceful degradation

## Quick Reference

### File Locations
- Main app: `app/main.py`
- Models: `app/models.py`
- Templates: `app/templates/`
- Tests: `tests/`
- Content: `app/content/`
- Scripts: `scripts/`

### Key Functions
- `ContentManager.get_mixed_content()`: Main content aggregator
- `parse_markdown_with_frontmatter()`: Content parser
- `timed_lru_cache()`: Caching decorator

### Environment Variables
- `ANTHROPIC_API_KEY`: AI features
- `USE_COMPILED_CSS`: CSS optimization
- `ENABLE_GARDEN_PATHS`: Feature flag

## Debugging Tips

### Common Issues
1. **Cache not updating**: Wait 5 minutes or restart server
2. **CSS not loading**: Run `npm run build:css`
3. **Tests failing**: Check async fixtures
4. **Content not showing**: Validate YAML frontmatter

### Debug Commands
```bash
# Check server logs
uvicorn app.main:app --reload --log-level debug

# Test specific endpoint
httpx http://localhost:8000/api/mixed

# Validate content
uv run python scripts/validate_frontmatter.py
```

This configuration will be automatically loaded by Claude Code agents to provide project-specific context and guidance.