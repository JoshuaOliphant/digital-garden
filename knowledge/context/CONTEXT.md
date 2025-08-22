# CONTEXT - Digital Garden Project Context

## Project Status
**Phase**: Active Development  
**Version**: 0.1.0  
**Last Updated**: 2025-08-16

## Current Work
Working on implementing a sliding panel navigation system for content exploration. The panels should allow users to navigate through related content in a natural, exploratory way similar to Andy Matuschak's notes.

## Recent Changes
- Implemented topographical homepage layout with garden metaphor
- Added feature flag system for gradual feature rollout
- Created comprehensive logging system
- Built Garden Paths navigation system
- Started sliding panel implementation

## Architecture Decisions

### Content Management
- File-based storage using Markdown with YAML frontmatter
- No database required, simplifying deployment and backup
- Content types: notes, bookmarks, TIL, how-to guides
- Growth stages: Evergreen, Budding, draft

### Frontend Approach
- Server-side rendering with Jinja2 for SEO and performance
- HTMX for progressive enhancement without JavaScript framework
- Tailwind CSS for utility-first styling
- Mobile-first responsive design

### Caching Strategy
- 5-minute TTL for content caching
- LRU cache with time-based expiration
- GitHub API responses cached to avoid rate limits
- Graceful degradation on cache misses

### Testing Philosophy
- Test-driven development for new features
- Async tests for FastAPI endpoints
- Model validation as first line of defense
- Integration tests for critical paths

## Performance Metrics
- Page load: < 1 second target
- Content cache hit rate: ~80%
- CSS bundle size: < 50KB minified
- Server response time: < 100ms p95

## Known Issues
1. CSS hot reload sometimes requires manual refresh
2. Cache invalidation is time-based only
3. Large content collections may need pagination optimization
4. Test coverage needs improvement in edge cases

## Dependencies & Constraints
- Python 3.12+ required for latest async features
- uv for fast, reliable dependency management
- Fly.io deployment requires Docker configuration
- GitHub API has rate limits (60/hour unauthenticated)

## Integration Points
- **GitHub API**: Fetches stars for project bookmarks
- **Anthropic API**: Content analysis and enhancement
- **Fly.io**: Production deployment platform
- **Logfire**: Observability and monitoring

## Security Considerations
- HTML sanitization with bleach library
- Environment variables for sensitive data
- No user authentication currently required
- Content validation at model level

## Future Considerations
- Consider adding full-text search with Elasticsearch/Meilisearch
- Evaluate static site generation for better performance
- Implement content versioning system
- Add collaborative editing features
- Consider GraphQL API for flexible querying

## Team Notes
- Single developer project
- Open to contributions
- Focus on simplicity and maintainability
- Progressive enhancement philosophy

## Environment Setup
```bash
# Required environment variables
ANTHROPIC_API_KEY=sk-ant-...
USE_COMPILED_CSS=true
ENABLE_GARDEN_PATHS=true

# Development
uvicorn app.main:app --reload --port 8000
npm run watch:css

# Testing
pytest

# Deployment
fly deploy
```

## Success Metrics
- Content discovery improvement
- Page load performance
- User engagement (time on site)
- Content quality scores
- SEO ranking improvements

## Risk Factors
- Content scaling beyond file system limits
- API rate limiting impacts
- CSS compilation complexity
- Cache coherency issues

## Communication Channels
- GitHub Issues for bug reports
- Pull requests for contributions
- Project documentation in `/docs`

This context should be reviewed and updated regularly as the project evolves.