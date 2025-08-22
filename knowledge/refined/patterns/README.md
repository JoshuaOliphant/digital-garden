# Validated Patterns
<!-- Proven, reusable patterns from this project -->

## Pattern Categories

### 1. **HTMX Integration Patterns**
See: [htmx_patterns.md](htmx_patterns.md)
- Server-side rendering with dynamic updates
- Partial template rendering
- Form submission patterns

### 2. **Growth Stage Patterns**
- Single source of truth via GrowthStageRenderer service
- Server-side injection of growth symbols
- Consistent theming across all routes

### 3. **Content Management Patterns**
- ContentService with IContentProvider interface
- Timed LRU caching (5-minute TTL)
- Mixed content aggregation
- YAML frontmatter validation with Pydantic models

### 4. **Testing Patterns**
See: [../solutions/testing/test_strategies.md](../solutions/testing/test_strategies.md)
- TDD RED-GREEN-REFACTOR cycle
- Comprehensive test coverage before implementation
- Fixture-based testing for content

---
*Add new validated patterns with evidence of successful use*