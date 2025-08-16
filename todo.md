# Digital Garden Implementation Todo List

## Phase 1: Foundation (Week 1-2)

### CSS & Infrastructure
- [x] **Task 1: CSS Pipeline Unification** ✅
  - Complexity: 2/5 | Dependencies: None
  - Remove Tailwind CDN, set up compiled CSS pipeline
  - Implement feature flag system
  - **Completed**: 2025-08-09
  - **Implementation Details**:
    - Created FeatureFlags class with USE_COMPILED_CSS environment variable
    - Modified base.html with conditional CSS loading (CDN vs compiled)
    - Synchronized tailwind.config.js with CDN configuration
    - Added 27 comprehensive tests following TDD principles
    - Zero breaking changes - defaults to CDN mode

- [x] **Task 2: Growth Stages Data Model** ✅
  - Complexity: 2/5 | Dependencies: Task 1
  - Extend BaseContent model with growth stages
  - Add vocabulary changes (planted/tended)
  - **Completed**: 2025-08-10
  - **Implementation Details**:
    - Created GrowthStage enum (seedling, budding, growing, evergreen)
    - Extended BaseContent with growth_stage, tended_count, garden_bed, connections fields
    - Implemented vocabulary helper for created→planted, updated→tended mapping
    - Added 28 comprehensive tests following TDD principles
    - Full backward compatibility maintained

- [x] **Task 3: Dark Mode Toggle** ✅
  - Complexity: 2/5 | Dependencies: Task 1
  - Implement theme switcher with localStorage
  - Create garden color palette
  - **Completed**: 2025-08-10
  - **Implementation Details**:
    - Fixed dark mode toggle with proper Alpine.js method calls
    - Implemented garden color palette (sage, earth, sky, sunset)
    - Theme persists across page reloads using localStorage
    - All components support dark mode with bg-garden-surface

- [x] **Task 4: Design System Components** ✅
  - Complexity: 3/5 | Dependencies: Tasks 2, 3
  - Create garden-themed components
  - Implement growth stage indicators
  - **Completed**: 2025-08-10
  - **Implementation Details**:
    - Created reusable Jinja2 macro templates (garden.html, typography.html, accessibility.html, layout.html)
    - Implemented growth stage indicators with emoji mapping (🌱 Seedling, 🌿 Budding, 🌳 Evergreen)
    - Created unified layout system with page_container, content_layout, prose_content macros
    - Added 112 comprehensive tests following TDD principles
    - Unified all templates to use consistent centered max-width layout
    - Extracted common elements to reduce special-case styling

## Phase 2: Topographical Navigation (Week 3-4)

### Navigation & Organization
- [ ] **Task 5: Topics Index Page**
  - Complexity: 3/5 | Dependencies: Task 4
  - Create /topics route with tag clustering
  - Implement HTMX filtering

- [ ] **Task 6: Garden Paths System**
  - Complexity: 3/5 | Dependencies: Task 4
  - Define path data structure
  - Create curated paths with progress tracking

- [x] **Task 7: Enhanced Homepage Layout** ✅
  - Complexity: 3/5 | Dependencies: Tasks 5, 6
  - Replace linear feed with topographical layout
  - Implement "Recently tended" section
  - **Completed**: 2025-08-12
  - **Implementation Details**:
    - Fixed datetime serialization error preventing homepage from loading
    - Implemented 3-column masonry layout with CSS columns for desktop
    - Replaced Alpine.js client-side rendering with server-side Jinja2 rendering
    - Added Maggie Appleton-inspired growth stage gradients and styling
    - Homepage now displays content count ("41 notes growing")
    - Content flows naturally in masonry grid from left to right columns

## Phase 3: Sliding Notes Interface (Week 5-6)

### Core Interface
- [x] **Task 8: HTMX-Only Interactions** ✅
  - Complexity: 3/5 | Dependencies: Task 1
  - Implement pure HTMX without Alpine.js
  - Server-side state management
  - **Completed**: 2025-08-14
  - **Implementation Details**:
    - Removed Alpine.js dependency entirely
    - Implemented dropdown functionality with pure HTMX
    - Created server-side endpoints for filtering and pagination
    - Added partial templates for dynamic content loading
    - All interactions now work without JavaScript

- [x] **Task 9: URL State Management** ✅
  - Complexity: 4/5 | Dependencies: Task 8
  - Implement garden-walk endpoint
  - Add browser history support
  - **Completed**: 2025-08-14
  - **Implementation Details**:
    - Created /garden-walk endpoint with query parameter support
    - Implemented serialize_garden_state() and deserialize_garden_state() functions
    - Added path (comma-separated IDs), focus (panel index), and view (display mode) parameters
    - Integrated browser History API with popstate event handling
    - URL length validation to stay under 2000 character limit
    - Handles invalid parameters gracefully with defaults
    - Supports bookmarkable and shareable URLs

- [x] **Task 10: Sliding Panel UI** ✅
  - Complexity: 4/5 | Dependencies: Task 9
  - Create panel components with animations
  - Add keyboard navigation
  - **Completed**: 2025-08-14
  - **Implementation Details**:
    - **ARCHITECTURAL CHANGE**: Andy Matuschak-style accordion navigation
    - Created panel-navigation.js with PanelManager class for dynamic panel opening
    - Internal hyperlinks open content in sliding panels automatically (inspired by notes.andymatuschak.org)
    - Horizontal accordion layout with panels side-by-side (not overlapping)
    - Fixed-width panels (660px) that maintain size regardless of depth
    - Unlimited panels can be opened - no artificial limit
    - Horizontal scrolling container to navigate between panels
    - Smooth CSS transitions with GPU acceleration (transform3d, will-change)
    - Keyboard navigation: ESC closes panel, arrow keys scroll between panels
    - Clean minimal design with focus on content readability
    - Panels persist until explicitly closed by user
    - Close buttons on each panel with proper focus management
    - Full accessibility with ARIA labels and keyboard support
    - URL state synchronization for bookmarkable reading paths
    - Removed dependency on predefined GARDEN_PATHS configuration

- [ ] **Task 11: Mobile Adaptation**
  - Complexity: 3/5 | Dependencies: Task 10
  - Vertical stack layout for mobile
  - Touch gesture support

- [ ] **Task 12: Panel State Synchronization**
  - Complexity: 4/5 | Dependencies: Tasks 10, 11
  - HTMX + Alpine.js sync
  - Share functionality

## Phase 4: Content Relationships (Week 7)

### Connections & Discovery
- [ ] **Task 13: Bidirectional Linking**
  - Complexity: 3/5 | Dependencies: Task 2
  - Parse internal links
  - Generate backlinks with preview popovers

- [ ] **Task 14: Related Content Discovery**
  - Complexity: 3/5 | Dependencies: Task 13
  - Tag-based relationships
  - Companion plants section

- [ ] **Task 15: Knowledge Graph (Optional)**
  - Complexity: 4/5 | Dependencies: Task 14
  - D3.js visualization
  - Interactive navigation

## Phase 5: Garden Features (Week 8)

### Special Features
- [ ] **Task 16: Garden Statistics Dashboard**
  - Complexity: 2/5 | Dependencies: Task 7
  - Create /garden-stats route
  - Implement metrics tracking

- [ ] **Task 17: Special Garden Areas**
  - Complexity: 2/5 | Dependencies: Task 2
  - Digital greenhouse (drafts)
  - Compost bin (archived)

- [ ] **Task 18: Interactive Elements**
  - Complexity: 3/5 | Dependencies: Task 4
  - Wander button
  - Growth animations

- [ ] **Task 19: Path Analytics**
  - Complexity: 3/5 | Dependencies: Task 9
  - Track path usage
  - Completion rates

## Phase 6: SEO & Performance (Week 9)

### Optimization
- [ ] **Task 20: SEO Metadata Engine**
  - Complexity: 3/5 | Dependencies: Task 2
  - Meta tag generation
  - Schema.org structured data

- [ ] **Task 21: Dynamic Sitemap**
  - Complexity: 2/5 | Dependencies: Task 20
  - XML generation with growth stage priorities
  - Crawlability optimization

- [ ] **Task 22: Performance Optimization**
  - Complexity: 3/5 | Dependencies: Task 20
  - Core Web Vitals optimization
  - Resource hints and lazy loading

## Progress Tracking

### Completed Tasks

#### Phase 1: Foundation
- [x] **Task 1: CSS Pipeline Unification** (2025-08-09)
  - Successfully migrated from Tailwind CDN to compiled CSS with feature flags
  - Implemented TDD with 27 tests (all passing)
  - Zero breaking changes achieved

- [x] **Task 2: Growth Stages Data Model** (2025-08-10)
  - Extended BaseContent with growth stages and garden vocabulary
  - Implemented TDD with 28 tests (all passing)
  - Full backward compatibility maintained

- [x] **Task 3: Dark Mode Toggle** (2025-08-10)
  - Fixed and implemented dark mode theme switching
  - Garden color palette integrated throughout
  - Theme persistence working correctly

- [x] **Task 4: Design System Components** (2025-08-10)
  - Created complete macro template system
  - Implemented TDD with 112 tests (all passing)
  - Unified layout across all page types
  - Garden metaphors integrated throughout

- [x] **Task 7: Enhanced Homepage Layout** (2025-08-12)
  - Fixed critical JSON serialization bug preventing homepage from loading
  - Implemented masonry layout with exactly 3 columns on desktop
  - Architectural decision: Replaced Alpine.js with server-side rendering for reliability
  - Integrated Maggie Appleton-inspired styling throughout

### Current Sprint
_Phase 2: Topographical Navigation - IN PROGRESS_
_Task 7 completed ahead of schedule during homepage bug fix session_

### Blocked Tasks
_Any blocked tasks and their blockers will be listed here_

## Notes

### Key Principles
- Write tests FIRST (TDD)
- No breaking changes
- Each task integrates immediately (no orphaned code)
- All states are URL-driven (bookmarkable)
- Features degrade gracefully

### Success Criteria
- [ ] All 22 tasks completed with tests passing
- [ ] Zero breaking changes to existing functionality
- [ ] Page load time < 2 seconds
- [ ] Lighthouse score > 90
- [ ] Core Web Vitals passing
- [ ] Test coverage > 80%
- [ ] Cross-browser compatibility verified

### Risk Items to Monitor
1. Alpine.js + HTMX integration complexity
2. URL length limits for garden walks
3. Mobile gesture performance
4. SEO impact from dynamic content

### Rollback Strategy
- Feature flags for all new features
- Gradual percentage-based rollout
- One-command rollback script available
- Backups before each deployment

---

**Last Updated**: 2025-08-14
**Total Tasks**: 22
**Completed**: 8/22 (36%)
**Estimated Timeline**: 9-10 weeks
**Current Phase**: Phase 3 - Sliding Notes Interface