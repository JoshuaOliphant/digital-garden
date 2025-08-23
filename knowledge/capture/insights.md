# Knowledge Capture - Digital Garden

## 2025-08-23 - Growth Stage Legend Implementation
**Project/Component**: Digital Garden UI Enhancement
**Confidence**: High

### Discoveries

#### Pattern: Contextual Help Integration
- **Context**: Users need to understand visual symbols without documentation
- **Evidence**: Growth stage symbols (•, ◐, ●, ■) used throughout site with no explanation
- **Solution**: Unobtrusive legend placed at bottom of relevant pages
- **Principle**: Contextual help should be discoverable but not intrusive

#### Pattern: Reusable UI Components via Macros
- **Context**: Need consistent legend across multiple pages
- **Evidence**: Legend needed on homepage, TIL page, tag pages
- **Solution**: Jinja2 macro `growth_stage_legend()` in shared macros file
- **Principle**: Single source of truth for UI components via macros

#### Pattern: Visual Progression Communication
- **Context**: Representing content maturity stages visually
- **Evidence**: Unicode symbols + color coding effectively convey progression
- **Solution**: • → ◐ → ● → ■ with corresponding color intensity increase
- **Principle**: Combine shape and color for redundant visual communication

### Implementation Details

**Macro Structure:**
```jinja2
{% macro growth_stage_legend() -%}
<div class="text-center py-6 border-t border-garden-border mt-8">
  <h3 class="text-sm font-medium text-garden-text-secondary mb-3">Growth Stages</h3>
  <div class="flex flex-wrap justify-center gap-6 text-sm">
    <!-- Legend items with symbol + description -->
  </div>
</div>
{%- endmacro %}
```

**Integration Pattern:**
1. Import: `{% from 'macros/garden.html' import growth_stage_legend %}`
2. Place after main content: `{{ growth_stage_legend() }}`
3. Only on pages showing growth symbols

### Challenges Resolved

#### Challenge: Legend Placement
- **Problem**: Where to place legend without cluttering interface
- **Solution**: Bottom of page after main content, separated by border
- **Rationale**: Provides context without interrupting content flow

#### Challenge: Which Pages Need Legend
- **Problem**: Not all pages show growth symbols
- **Solution**: Selectively added to homepage, TIL, and tag pages only
- **Rationale**: Only show where relevant to avoid confusion

### Generalizable Principles

1. **Contextual Help Placement**: Place explanatory content at page bottom to inform without interrupting
2. **Macro Architecture**: Use template macros for reusable UI components
3. **Visual Hierarchy**: Use borders and spacing to separate supplementary content
4. **Progressive Disclosure**: Provide information where needed, not everywhere
5. **Redundant Encoding**: Use both shape and color for important visual distinctions

### Related Patterns
- Template macro organization
- User experience for symbol legends
- Dark theme UI component design
- Responsive flex layouts

---

## 2025-08-23 - Comprehensive Codebase Cleanup
**Project/Component**: Digital Garden Maintenance
**Confidence**: High

### Discoveries

#### Pattern: Dead Code Detection
- **Context**: FastAPI routes that look valid but aren't registered
- **Evidence**: 600+ lines of route handlers in main.py not in routers
- **Solution**: Check router registration, not just function signatures
- **Principle**: Verify code is actually reachable, not just syntactically correct

#### Pattern: JavaScript to CSS Migration
- **Context**: Simple UI interactions using JavaScript unnecessarily
- **Evidence**: Checkbox styling, responsive menus using JS
- **Solution**: CSS `:checked` selectors, Tailwind responsive classes
- **Principle**: Prefer CSS-only solutions for styling and simple interactions

#### Pattern: Template Consolidation
- **Context**: Templates with unnecessary indirection
- **Evidence**: til.html just extending base and including partials/til.html
- **Solution**: Consolidate into single template
- **Principle**: Eliminate unnecessary template layers

### Successful Approaches

1. **Systematic Verification**: grep entire codebase before removing "unused" code
2. **Router-First Architecture**: All routes through proper router files
3. **CSS-First Interactions**: Modern CSS can replace most simple JavaScript
4. **Import Cleanup**: Remove imports after removing code that used them

### Code Removal Statistics
- **Lines Removed**: 1,103
- **Lines Added**: 154
- **Net Reduction**: 949 lines (86% reduction)
- **Files Deleted**: 3 template files

### Lessons Learned

1. **Dead Code Accumulation**: Routes get moved to routers but originals remain
2. **Template Sprawl**: Partials can proliferate unnecessarily
3. **JavaScript Overuse**: Many interactions better handled by CSS
4. **Import Hygiene**: Unused imports accumulate over time

### Anti-patterns Identified

1. **Partial Templates Extending Base**: Partials should be include-only
2. **Empty JavaScript Blocks**: Remove rather than leave empty
3. **Undefined CSS Classes**: Always verify custom classes exist
4. **Duplicate Template Logic**: Same content in multiple template files