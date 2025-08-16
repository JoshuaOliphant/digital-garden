# Plain Text Digital Garden Specification

## Executive Summary

A radically simple, text-first digital garden that combines the minimalist aesthetic of plain text blogs with sophisticated content exploration through URL-driven path accumulation. Built on FastAPI and HTMX, this system prioritizes content and connections over interface complexity.

**Core Philosophy:** Content and connections are the interface. Remove all visual noise that doesn't serve the ideas.

## Vision & Goals

### Primary Goal
Create a personal knowledge garden for public learning where Joshua can write about ongoing projects and interesting discoveries, with a focus on developer-friendly, text-based workflows.

### Key Principles
- **Radical simplicity** - Typography and content structure are the primary design elements
- **URL-driven exploration** - Every reading journey is bookmarkable and shareable
- **Manual curation** - Author maintains full control over connections and growth stages
- **Clean codebase** - No backward compatibility concerns, remove all unused code

## User Audience

### Primary User
- **Joshua (Author)**: Developer who writes in markdown, uses git-based workflows, and values simplicity

### Secondary Audience  
- **Readers**: People discovering content through search, interested in technical topics, who value easy content extraction and sharing

## Core Features (MVP)

### 1. Path-Accumulating Navigation
- URLs track complete exploration journey: `/explore?path=docker-basics,ci-cd-pipelines,python-testing`
- Each step in path is accessible by URL manipulation
- Maximum path length: 10 notes
- Circular path prevention
- Graceful handling of invalid paths (show last valid note with error)

### 2. Automatic Backlinks
- "Mentioned in" section on each note
- Calculated from manual hyperlinks in content
- Bidirectional connection discovery

### 3. Growth Stage Indicators
- Visual progression using minimal symbols:
  - • = seedling (new idea)
  - ◐ = budding (developing)
  - ● = growing (substantial)
  - ■ = evergreen (mature/stable)
- Set manually in frontmatter as words: `growth: "seedling"`
- Converted to symbols during rendering

### 4. Tag-Based Discovery
- Existing tag system preserved
- Filter by single or multiple tags
- Tag pages showing all related content

### 5. RSS Feed
- Full content in feeds
- Include growth stage in feed metadata
- Separate feeds per content type (optional)

### 6. Syntax Highlighting
- Code blocks with language-specific highlighting
- Dark theme optimized colors
- Support for common languages (Python, JavaScript, etc.)

## Content Structure

### Content Types (Preserved)
- **Notes**: Long-form articles and documentation
- **Bookmarks**: External links and references (open in new tabs)
- **TIL**: Today I Learned quick notes
- **Projects**: Project pages (standalone, not in exploration paths)
- **Now**: Current focus page (standalone)
- **Pages**: Static pages like About

### URL Structure
```
/                           → Homepage with recent content
/explore?path=note1,note2   → Exploration with path accumulation
/notes/{slug}              → Direct note access (starts new path)
/tags/{tag}                → Tag filtered view
/feed.xml                  → RSS feed
```

### Frontmatter Schema
```yaml
---
title: "Required title"
created: "2024-03-14"
updated: "2024-03-15"
tags: [python, testing, docker]
growth: "seedling"  # seedling|budding|growing|evergreen
type: "note"  # note|bookmark|til
---
```

## Visual Design

### Typography & Layout
```css
/* Dark theme with technical typography */
body {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  background: #1a1a1a;
  color: #e0e0e0;
  max-width: 65ch;
  margin: 0 auto;
  padding: 2rem 1rem;
  line-height: 1.6;
}

/* Growth stages as minimal symbols */
.growth-seedling::before { content: "• "; opacity: 0.6; }
.growth-budding::before { content: "◐ "; opacity: 0.7; }
.growth-growing::before { content: "● "; opacity: 0.8; }
.growth-evergreen::before { content: "■ "; opacity: 1.0; }
```

### Content Differentiation
- Subtle visual indicators for content types (if feasible while maintaining simplicity)
- Otherwise, keep uniform appearance
- Growth stage symbols provide primary visual hierarchy

## Technical Architecture

### Stack
- **Backend**: FastAPI (existing)
- **Frontend**: HTMX for smooth navigation
- **Styling**: Plain CSS (remove Tailwind)
- **Markdown**: Python-markdown with frontmatter
- **Syntax Highlighting**: Pygments
- **Deployment**: Fly.io (existing)
- **CI/CD**: GitHub Actions (existing)

### Key Implementation Details

#### Path Management
```python
@app.get("/explore")
async def explore(
    request: Request,
    path: str = Query("", max_length=500),  # URL length limit
):
    notes = path.split(",")[:10] if path else []  # Max 10 notes
    
    # Validate path and prevent circles
    valid_notes = []
    seen = set()
    for note in notes:
        if note not in seen and note_exists(note):
            valid_notes.append(note)
            seen.add(note)
        else:
            break  # Stop at first invalid/circular reference
    
    current_note = valid_notes[-1] if valid_notes else None
    
    return templates.TemplateResponse("explore.html", {
        "note": get_note(current_note),
        "breadcrumb": valid_notes,
        "backlinks": get_backlinks(current_note),
        "related": get_related_by_tags(current_note),
        "path_string": ",".join(valid_notes)
    })
```

#### Backlink Calculation
```python
def get_backlinks(note_slug: str) -> List[Note]:
    """Find all notes that link to this note"""
    backlinks = []
    for other_note in get_all_notes():
        if note_slug in extract_internal_links(other_note.content):
            backlinks.append(other_note)
    return backlinks
```

### Performance Strategy
- Cache rendered markdown → HTML (if rendering is slow)
- Cache invalidation on file change (rare updates)
- Preload hover preview content on page load
- Target: < 2 second page loads

### Mobile Adaptations
- Compressed breadcrumb showing: Previous → Current → Next
- Touch-friendly tap targets
- Responsive typography scaling
- Horizontal scroll for long code blocks

## Nice-to-Have Features (Future)

1. **Hover Previews**: Show first paragraph of linked notes on hover
2. **Reading Time**: Estimates based on word count
3. **Share Trail Button**: Copy exploration URL to clipboard
4. **Search**: Full-text search across all content
5. **Related Content**: Suggestions based on shared tags
6. **Random Wander**: Button for serendipitous discovery

## Migration Plan

### Phase 1: Clean Slate Setup (Week 1)
1. Remove all unused code (sliding panels, complex JavaScript)
2. Strip down to FastAPI + basic templates
3. Implement new dark theme CSS
4. Set up exploration route structure

### Phase 2: Core Features (Week 2)
1. Path accumulation navigation
2. Backlink calculation system
3. Growth stage rendering
4. Tag-based filtering

### Phase 3: Content Migration (Week 3)
1. Add growth stages to all existing content
2. Update all internal links to use slugs
3. Ensure all content types work in new system
4. Test exploration paths thoroughly

### Phase 4: Polish & Launch (Week 4)
1. Mobile responsive testing
2. Performance optimization (add caching if needed)
3. RSS feed updates
4. Deploy to production

## Development Workflow

### Local Development
```bash
# Start dev server
uvicorn app.main:app --reload --port 8000

# Test exploration paths
curl "http://localhost:8000/explore?path=note1,note2,note3"
```

### Content Workflow
1. Write markdown files in VS Code/Cursor
2. Set frontmatter including growth stage
3. Add manual hyperlinks to related content
4. Push to git
5. GitHub Actions deploys to Fly.io

### Growth Stage Reference
```yaml
# Copy this reference for frontmatter:
growth: "seedling"   # • - New idea, just planted
growth: "budding"    # ◐ - Developing, taking shape  
growth: "growing"    # ● - Substantial, maturing
growth: "evergreen"  # ■ - Mature, stable, reference-worthy
```

## Success Metrics

### Technical
- [ ] All existing content accessible
- [ ] Page loads < 2 seconds
- [ ] Clean URLs with path accumulation working
- [ ] Backlinks automatically calculated
- [ ] Mobile responsive design
- [ ] No JavaScript errors
- [ ] All old/unused code removed

### User Experience  
- [ ] Clear navigation through exploration paths
- [ ] Easy to share specific journeys
- [ ] Content remains highly readable
- [ ] Code blocks properly highlighted
- [ ] Growth stages visible but not distracting

## Code Cleanup Targets

### Remove
- All sliding panel JavaScript (`panel-navigation.js`)
- Alpine.js dependencies
- Tailwind CSS configuration
- Complex state management code
- Unused templates and partials
- Any dark mode toggle code (single theme only)

### Simplify
- Reduce template complexity
- Remove unnecessary API endpoints
- Consolidate CSS into single file
- Streamline model definitions

## Testing Requirements

### Core Functionality
- Path accumulation with various note combinations
- Backlink detection accuracy
- Tag filtering with multiple tags
- Growth stage display
- URL validation and error handling
- Mobile responsive behavior

### Edge Cases
- Circular path attempts
- Non-existent notes in paths
- Very long paths (>10 notes)
- Special characters in slugs
- Empty content handling

## Security Considerations

- Sanitize all URL parameters
- Prevent path traversal attacks
- Rate limiting on expensive operations (backlink calculation)
- XSS prevention in markdown rendering

## Documentation Needs

- README update with new navigation model
- Growth stage guidelines for content
- URL structure documentation
- Deployment instructions remain unchanged

---

**Document Version:** 1.0  
**Created:** 2024-03-14  
**Author:** Joshua Oliphant  
**Status:** Ready for Implementation

## Next Steps

1. Review and approve this specification
2. Create implementation plan with specific tasks
3. Begin Phase 1: Clean Slate Setup
4. Set up development branch for new system