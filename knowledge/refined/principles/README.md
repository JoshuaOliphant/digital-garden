# Core Principles
<!-- Fundamental project principles and architectural decisions -->

## Established Principles

### 1. **Single Source of Truth**
Every piece of domain knowledge should have exactly one authoritative source:
- Growth stage symbols: GrowthStageRenderer service
- Content metadata: YAML frontmatter in markdown files
- Styling: CSS custom properties in main.css

### 2. **Server-Side Rendering First**
- Use HTMX for dynamic updates without full JavaScript frameworks
- Render content server-side for better SEO and performance
- Progressive enhancement over client-side complexity

### 3. **Content as Data**
- Markdown files are the primary data source
- YAML frontmatter provides structured metadata
- File system organization reflects content hierarchy

### 4. **Test-Driven Development**
- Write failing tests first (RED)
- Implement minimal code to pass (GREEN)
- Refactor for quality (REFACTOR)
- Never skip the test phase

### 5. **Dark Theme by Default**
- Design for dark theme (#1a1a1a background)
- High contrast for readability
- Consistent color palette via CSS variables

---
*Core principles guide all architectural and implementation decisions*