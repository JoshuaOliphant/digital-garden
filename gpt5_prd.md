## Product Requirements Document (PRD)
Digital Garden Modernization and “Explore” Wandering Mode

### Background
Redesign the blog to embody the digital garden ethos—topography over timelines, continuous growth, imperfection in public—while delivering a modern, fast, and accessible reading experience. Inspiration: Maggie Appleton’s essay and garden.

- A Brief History & Ethos of the Digital Garden: https://maggieappleton.com/garden-history
- Maggie’s Garden: https://maggieappleton.com/garden/
 - Bookmarkable by Design: URL‑Driven State in HTMX: https://www.lorenstew.art/blog/bookmarkable-by-design-url-state-htmx/

### Goals
- Surface the garden ethos in UI and language.
- Improve readability, dark mode, and performance.
- Enable topographical exploration: topics, paths, backlinks, related notes.
- Add an optional multi‑pane “Explore” mode for wandering laterally.
- Preserve current stack and content structure; minimize backend changes.

### Non‑Goals
- Building a headless CMS or admin authoring UI.
- Replacing FastAPI/Jinja/HTMX/Tailwind stack.
- Implementing heavy knowledge graph or analytics in v1 (deferrable).

### Users and Jobs
- Reader‑explorer: wander, follow links, browse by topic, skim related notes.
- Returning reader: see recently tended notes and status.
- Author: keep content simple (Markdown + frontmatter), avoid extra fields.

### Success Metrics
- Increase page depth (avg panes opened or pages/session) by 20%.
- 50%+ of content views originate from topography (tags/paths) or backlinks/related.
- CLS < 0.1, LCP < 2.5s on home and content pages.
- Dark mode usage > 25%.
- No increase in error rate or test failures.

---

## Scope

### Phase 0 — Design System Foundation
- Unify Tailwind build:
  - Remove CDN script from `templates/base.html`; use compiled `app/static/css/output.css`.
  - Dev: `npm run watch:css`; build: `npm run build:css`.
- Typography and color:
  - Calm type scale; warm neutrals + emerald/sage accent.
  - Dark mode toggle (persists in localStorage; `dark` class on `html`).
- Language:
  - Replace “Created/Updated” with “Planted/Last tended”.
  - Display status chips consistently.

Deliverables
- Updated `base.html`, `index.html`, `content_page.html`, `partials/content_card.html`.
- New dark mode toggle script; no framework changes.

### Phase 1 — Reading & Browsing Experience
- Cards: refined spacing, subtle shadows, status chips; show “Planted”.
- Content pages: improved meta strip; consistent `prose` usage; optional reading progress bar (long notes).
- Sticky TOC on wide screens only (uses current `TocExtension`).

Deliverables
- Updated templates above; optional `partials/toc.html`.

### Phase 2 — Topography Over Timelines
- Topic Index page: all tags with counts; HTMX filters (type, status).
- Curated Paths: `pages/path-*.md` for manual sequences; CTA from home.
- “Wander”: random note endpoint.

Deliverables
- Routes/pages: `GET /topics`, `GET /paths`, `GET /wander`.
- Templates: `templates/topics.html`, `templates/paths.html`.

### Phase 3 — Garden Mechanics
- Backlinks: parse internal links during render; show “Referenced by” list.
- Related notes: based on shared tags + link overlap (3–5 items).
- Internal link previews: hover popover (HTMX partial fetch; short excerpt).

Deliverables
- Render step that marks internal links and extracts link graph in memory.
- `partials/backlinks.html`, `partials/related.html`, `partials/link_preview.html`.

### Phase 4 — Explore Mode (Multi‑Pane Wandering)

Behavior
- Clicking an internal link inside pane i:
  - If i is not rightmost, replace pane i+1 and drop any panes to the right.
  - If i is rightmost, append a new pane to the right.
- Horizontal scroll with snap; arrow keys navigate; close button removes panes to the right; external links open normally.
- URL/state: encode stack (e.g., `/explore?stack=/notes/foo|/til/bar`), also save to `history.state` and `localStorage`.

Routes
- `GET /explore/{content_type}/{slug}` → full page with 1 pane.
- `GET /explore/pane/{content_type}/{slug}` → `partials/pane.html` only.

Templates
- `templates/explore.html` (horizontal container `#note-strip`).
- `templates/partials/pane.html` (single note pane).

Client
- Small JS controller + HTMX: delegates clicks on `a[data-internal]`, appends/replaces panes, scrolls into view, updates history.
- Progressive enhancement: outside `/explore`, links behave normally.

Constraints
- Cap open panes (e.g., 7–9). Lazy-load images. Respect dark mode. A11y: focus management, `role="region"`, `aria-labelledby`.

### Phase 5 — Advanced (Deferred)
- Knowledge graph page (lazy-loaded D3; JSON nodes/edges).
- Minimal stats page (counts by status, recent tending timeline).
- Optional seasonal themes; custom 404 (“lost in the garden”).

---

## Functional Requirements

- Status model
  - Use single `status` field with allowed values: Seedling | Budding | Evergreen.
  - Display status chip in cards and content pages.

- Planted/Last tended
  - Map `created` → Planted; `updated` → Last tended (omit if same as planted).
  - Show in meta strips and RSS descriptions.

- Topography
  - Topic Index lists tags with counts; filters by `content_type` and `status`.
  - Paths are rendered from Markdown pages with ordered links.

- Backlinks/Related
  - Detect internal links in HTML; compile backlinks map per note.
  - Related list uses shared tags + link overlap.

- Explore Mode
  - Pane open/replace rules; snap scrolling; keyboard and close actions.
  - Shareable URLs with stack; restore from `localStorage`.

- Accessibility
  - Dark/light contrast compliant; focus states; keyboard navigation; skip link.

 - SEO
   - Per-page SEO: unique `<title>` and `<meta name="description">` from frontmatter; clean headings.
   - Open Graph AND Twitter Cards: set `og:type`, `og:title`, `og:description`, `og:url`, `og:image`, `og:site_name` and `twitter:card=summary_large_image`, `twitter:title`, `twitter:description`, `twitter:image`.
   - Canonicals and robots: canonical to stable URL on all indexable pages; `noindex,follow` for utility/stateful pages (e.g., `/explore`).
   - Structured data: JSON‑LD `BlogPosting` on content pages, `CollectionPage` on tag/topic pages, `WebSite` on home; include `datePublished`, `dateModified`, `keywords`.
   - Pagination: add `rel="prev"/"next"` links where applicable; lists expose a crawlable "Next" link in addition to HTMX triggers.
   - Sitemap/RSS: keep sitemap with correct `lastmod`; RSS includes excerpt and links to canonical URLs.

---

## Non‑Functional Requirements

- Performance budgets
  - LCP < 2.5s on home/content; CLS < 0.1; JS for Explore < 10KB gzipped (excluding HTMX).
  - Lazy-load off-screen panes/images. Tree-shake Tailwind with correct content globs.

- Reliability
  - Existing tests remain green; add tests for new utilities (e.g., link parsing).

- Tooling
  - Use `uv` for Python; `npm` for CSS build only. Tailwind build must be deterministic.

---

## Architecture & IA

- No DB. Operate on Markdown + frontmatter in `app/content/**`.
- Build a transient in-memory link graph during render calls (derived from sanitized HTML).
- New templates: `explore.html`, `topics.html`, `paths.html`, `partials/pane.html`, `partials/backlinks.html`, `partials/related.html`, optional `partials/toc.html`.

---

## API/Routes (additions)
- GET `/topics` → topics index (HTMX compatible filters)
- GET `/paths` → curated path pages
- GET `/wander` → 302 to random content
- GET `/explore/{content_type}/{slug}` → multi‑pane page
- GET `/explore/pane/{content_type}/{slug}` → pane partial

No breaking changes to existing routes.

---

## Data Model
- Keep `BaseContent` fields. Standardize `status` values to {Seedling, Budding, Evergreen}.
- No new persistent fields. Use transient data for backlinks and related.

---

## Template Changes (high‑level)
- `base.html`: remove Tailwind CDN; include compiled CSS; add dark mode toggle and skip link.
- `index.html`: refine hero, grid cards, “Explore by topic” and “Follow a path” CTAs.
- `content_page.html`/`partials/content.html`: meta strip, tags, backlinks and related sections.
- `partials/content_card.html`: status chip, planted date, tag pills, “Open in Explore” secondary CTA.

---

## Client Behavior
- Mark internal links during Markdown conversion with `data-internal="true"`.
- Explore controller handles pane stack, history, focus, and scroll.
- HTMX continues to power partial fetches (pane HTML, previews, filters).

---

## URL‑Driven State (Cross‑Cutting)
- Treat the URL as the single source of truth for view state across filters, sorting, pagination, and Explore pane stacks.
- Server endpoints must read query params and render views accordingly (bookmarkable and reload‑safe).
- HTMX interactions:
  - Use `hx-push-url="true"` so history/back/forward work naturally.
  - Use `hx-params="*"` and/or `hx-include` to preserve full form state on requests.
  - Use hidden inputs for any state not directly controlled by the active UI element.
- Explore mode:
  - Encode `stack` (pipe‑delimited list of paths) and `focus` (active pane index) in the URL.
  - Each internal navigation updates these params via `hx-vals` + `hx-push-url`.
- Guardrails: validate/sanitize params; cap stack length to avoid oversized URLs; progressive enhancement if JS is disabled.

---

## SEO Optimization
- Meta and Canonical
  - Generate unique `<title>` and `<meta name="description">` from frontmatter (fallback to safe excerpt).
  - Include `<link rel="canonical" href="https://anoliphantneverforgets.com{{ request.url.path }}">`.
- Open Graph and Twitter Cards (use both)
  - `og:type` (`article` for notes/how‑tos/TIL, `website` for home), `og:title`, `og:description`, `og:url`, `og:image` (1200×630), `og:site_name`.
  - `twitter:card=summary_large_image`, `twitter:title`, `twitter:description`, `twitter:image`.
- JSON‑LD Structured Data
  - Content pages: `BlogPosting` with `headline`, `datePublished` (created), `dateModified` (updated), `keywords` (tags), `url`, optional `image`, `author`.
  - Topic index/tag pages: `CollectionPage` with `name`, `url`, `about`.
  - Home: `WebSite` with `url` and optional `SearchAction` when search ships.
- Pagination and Crawlability
  - On paginated pages (`/til`, topics), add `<link rel="prev">`/`<link rel="next">` and render a visible "Next page" anchor so crawlers can traverse beyond HTMX infinite scroll.
  - Encode filters/pagination in URL (works with URL‑driven state section) to keep pages bookmarkable and crawlable.
- Robots/Indexing Rules
  - `noindex,follow` on `/explore` and any highly stateful/duplicate pages; ensure canonical points to a stable URL if indexing is desired later.
- Images and Performance
  - Add `alt`, `width`/`height`, `loading="lazy"`; prefer WebP/AVIF for local assets; generate social default image.
- Feeds and Sitemaps
  - Keep `/sitemap.xml` up to date with `lastmod`; keep RSS/Atom feed with description/excerpt and canonical links.

## Accessibility
- Roles/labels on panes and controls; keyboard navigation (←/→, Esc).
- Color contrast verified in dark and light; focus-visible styles.
- Maintain heading order and landmarks; skip link to main content.

---

## Analytics/Telemetry (lightweight)
- Count “Open in Explore” clicks, average pane depth, backlinks click rate.
- Avoid third-party trackers; log minimal events server-side or via existing logging.

---

## Rollout Plan
- Milestone 1 (Foundation): unified Tailwind, dark mode, language changes.
- Milestone 2 (Reading): card/content polish, progress bar, TOC.
- Milestone 3 (Topography): topics, paths, wander.
- Milestone 4 (Mechanics): backlinks, related, link previews.
- Milestone 5 (Explore): multi‑pane explore with history/state.
- Milestone 6 (Advanced): graph, stats, 404.

---

## Risks & Mitigations
- Heavy JS/perf regressions → keep Explore controller tiny; lazy-load extras.
- URL/state complexity → encode stack simply; cap pane count.
- A11y in multi‑pane → explicit focus management; keyboard shortcuts; ARIA regions.
- Style drift between CDN and built CSS → remove CDN; CI build CSS consistently.

---

## Acceptance Criteria (examples)
- Foundation
  - Tailwind CDN removed; only `output.css` loaded; dark mode toggle persists.
  - “Planted/Last tended” visible on content pages; status chip renders everywhere.

- Topography
  - `/topics` lists tags with counts; filters update via HTMX without full reload.
  - Visiting `/paths` shows at least one curated path rendered from Markdown.
  - Back/forward/reload/bookmark reproduces the exact filtered/sorted/paged view; HTMX uses `hx-push-url` and preserves state via hidden inputs.

- Backlinks/Related
  - Opening a note shows backlinks when present; related section lists 3–5 items.

- Explore
  - `/explore/notes/<slug>` loads a single pane.
  - Clicking internal links appends or replaces panes per rule.
  - URL encodes `stack` and `focus`; reloading or sharing the link reconstructs panes and focused index; back/forward traverse pane history.

- Performance
  - Core pages meet performance budgets on a sample dataset.

- Tests
  - Existing tests pass; new unit tests for link parsing and related selection added.

- SEO
  - Content pages include unique Title/Description, Canonical, Open Graph and Twitter Card tags, and `BlogPosting` JSON‑LD.
  - Paginated lists include `rel prev/next` and a visible "Next page" link; filters/pagination reflected in the URL.
  - `/explore` is `noindex,follow` (or canonicalized) to avoid duplicate/stateful indexing.
  - Sitemap lists all indexable items with correct `lastmod`; RSS uses canonical URLs and excerpts.

---

## QA/Test Plan
- Unit tests:
  - Internal link detection from rendered HTML.
  - Backlink graph assembly.
  - Related-note selection logic.
- Integration (pytest + httpx):
  - `/topics` filters return partials; `/wander` redirects; `/explore/pane/...` returns valid HTML.
- Accessibility checks:
  - Keyboard-only navigation; dark/light contrast; ARIA roles in panes.
- Manual:
  - Explore stack limits, URL/history, localStorage restore, mobile horizontal scroll.

---

## Dependencies
- Tailwind build (`postcss`, typography plugin).
- HTMX (already included).
- No new Python deps required.

---

## Open Questions
- Should Explore mode be default from content pages, or remain a separate “Open in Explore” CTA?
- Do we want to show TOC in Explore panes or keep panes minimal?
- What max pane count feels right (7, 9)?

---

## References
- Maggie Appleton — A Brief History & Ethos of the Digital Garden: https://maggieappleton.com/garden-history
- Maggie’s Garden: https://maggieappleton.com/garden/
 - Bookmarkable by Design: URL‑Driven State in HTMX: https://www.lorenstew.art/blog/bookmarkable-by-design-url-state-htmx/


