# Architecture Decisions - Digital Garden

## ADR-001: File-Based Content Storage
**Date**: 2024-01-15  
**Status**: Accepted

### Context
Need a simple, portable content storage solution that doesn't require database setup.

### Decision
Use Markdown files with YAML frontmatter for all content storage.

### Consequences
- ✅ Simple backup and version control
- ✅ No database migrations
- ✅ Easy content editing
- ❌ Limited query capabilities
- ❌ Potential scaling issues with large collections

---

## ADR-002: Server-Side Rendering with HTMX
**Date**: 2024-02-01  
**Status**: Accepted

### Context
Need interactive UI without complex JavaScript framework overhead.

### Decision
Use Jinja2 templates with HTMX for progressive enhancement.

### Consequences
- ✅ Better SEO and initial load performance
- ✅ Works without JavaScript
- ✅ Simpler development model
- ❌ Less rich interactivity than SPA
- ❌ More server requests

---

## ADR-003: Time-Based Caching Strategy
**Date**: 2024-02-15  
**Status**: Accepted

### Context
Content reads are frequent but updates are relatively rare.

### Decision
Implement 5-minute TTL caching with LRU eviction.

### Consequences
- ✅ Reduced I/O and processing
- ✅ Predictable cache behavior
- ❌ Potential stale content for 5 minutes
- ❌ No immediate cache invalidation

---

## ADR-004: uv for Python Dependency Management
**Date**: 2024-03-01  
**Status**: Accepted

### Context
Need fast, reliable Python dependency management.

### Decision
Use uv instead of pip/poetry/pipenv.

### Consequences
- ✅ 10-100x faster installations
- ✅ Built-in virtual environment management
- ✅ Reproducible builds with lock files
- ❌ Newer tool with smaller community
- ❌ Team needs to learn new tool

---

## ADR-005: Pydantic for Data Validation
**Date**: 2024-03-15  
**Status**: Accepted

### Context
Need robust validation for content frontmatter.

### Decision
Use Pydantic models for all content types.

### Consequences
- ✅ Type safety and validation
- ✅ Automatic error messages
- ✅ JSON schema generation
- ❌ Additional dependency
- ❌ Learning curve for team