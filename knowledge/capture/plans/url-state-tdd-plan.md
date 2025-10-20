# TDD Implementation Plan: URL State Management for Digital Garden

## Executive Summary

Transform the Digital Garden into a fully bookmarkable, state-preserving web application where every view can be shared via URL. Implementation follows strict TDD principles with 15 incremental tasks organized in 5 phases.

## Architecture Overview

### Component Architecture
```
┌─────────────────────────────────────────────────┐
│                   User Interface                 │
├─────────────────────────────────────────────────┤
│  Filter Bar │ Quick Pills │ Sort Headers │ Search│
├─────────────────────────────────────────────────┤
│              URL State Controller                │
│  - Parameter parsing/validation                  │
│  - Default management                            │
│  - State serialization                           │
├─────────────────────────────────────────────────┤
│              Filter Service                      │
│  - Content filtering                             │
│  - Multi-criteria matching                       │
│  - Result aggregation                            │
├─────────────────────────────────────────────────┤
│              Content Service                     │
│  - Existing content retrieval                    │
│  - Enhanced with filter support                  │
└─────────────────────────────────────────────────┘
```

### Data Flow
```
URL Parameters → Parse & Validate → Apply Filters → Render with State → HTMX Updates URL
```

## Technology Stack
- **Backend**: FastAPI with enhanced Query parameter handling
- **Frontend**: HTMX with hx-push-url for URL management
- **Templates**: Jinja2 with state-aware macros
- **Testing**: pytest with async support, parameterized tests

## Phase 1: Foundation (Tasks 1-3)

### Task 1: URL Parameter Parser Service
**Complexity**: 3
**Test Units**: 8
**Dependencies**: None

**Tests to Write First**:
```python
def test_parse_empty_params_returns_defaults()
def test_parse_types_comma_separated()
def test_parse_tags_comma_separated()
def test_parse_growth_stages_comma_separated()
def test_parse_sort_field_with_validation()
def test_parse_order_direction_validation()
def test_parse_page_number_validation()
def test_parse_invalid_params_returns_defaults()
```

**Implementation**: Create `app/services/url_state.py` with `URLStateParser` class

---

### Task 2: Filter Service Core
**Complexity**: 4
**Test Units**: 10
**Dependencies**: Task 1

**Tests to Write First**:
```python
def test_filter_by_single_content_type()
def test_filter_by_multiple_content_types()
def test_filter_by_single_tag()
def test_filter_by_multiple_tags_intersection()
def test_filter_by_growth_stage()
def test_filter_by_combined_criteria()
def test_filter_excludes_drafts_by_default()
def test_filter_with_empty_criteria_returns_all()
def test_filter_preserves_content_structure()
def test_filter_performance_with_large_dataset()
```

**Implementation**: Create `app/services/content_filter.py` with `ContentFilterService` class

---

### Task 3: Sort Service
**Complexity**: 2
**Test Units**: 6
**Dependencies**: Task 2

**Tests to Write First**:
```python
def test_sort_by_created_date_desc()
def test_sort_by_created_date_asc()
def test_sort_by_updated_date()
def test_sort_by_title_alphabetical()
def test_sort_with_null_values()
def test_sort_maintains_stable_order()
```

**Implementation**: Extend `ContentFilterService` with sorting methods

## Phase 2: Core Routes (Tasks 4-7)

### Task 4: Enhanced Home Route with Filters
**Complexity**: 3
**Test Units**: 8
**Dependencies**: Tasks 1-3

**Tests to Write First**:
```python
async def test_home_route_without_params_shows_all()
async def test_home_route_with_type_filter()
async def test_home_route_with_tag_filter()
async def test_home_route_with_growth_filter()
async def test_home_route_with_sort_params()
async def test_home_route_preserves_state_in_template()
async def test_home_route_handles_invalid_params()
async def test_home_route_pagination_preserves_filters()
```

**Implementation**: Update `app/routers/main.py` home route

---

### Task 5: Filter Bar Template Component
**Complexity**: 4
**Test Units**: 7
**Dependencies**: Task 4

**Tests to Write First**:
```python
def test_filter_bar_renders_with_no_filters()
def test_filter_bar_shows_active_type_filters()
def test_filter_bar_shows_active_tag_filters()
def test_filter_bar_shows_active_growth_filters()
def test_filter_bar_generates_correct_htmx_attributes()
def test_filter_bar_preserves_hidden_state_fields()
def test_filter_bar_shows_filter_count_badge()
```

**Implementation**: Create `app/templates/components/filter_bar.html` macro

---

### Task 6: HTMX State Preservation
**Complexity**: 3
**Test Units**: 6
**Dependencies**: Task 5

**Tests to Write First**:
```python
def test_htmx_form_includes_all_params()
def test_htmx_push_url_updates_browser_url()
def test_htmx_params_star_includes_all_fields()
def test_htmx_trigger_on_change_for_filters()
def test_htmx_target_updates_content_area()
def test_htmx_preserves_state_across_requests()
```

**Implementation**: Update filter bar with HTMX attributes

---

### Task 7: Smart Sort Headers
**Complexity**: 3
**Test Units**: 6
**Dependencies**: Task 6

**Tests to Write First**:
```python
def test_sort_header_toggles_direction()
def test_sort_header_preserves_filters()
def test_sort_header_shows_current_sort_indicator()
def test_sort_header_resets_pagination()
def test_sort_header_htmx_vals_correct()
def test_multiple_sort_headers_coordinate()
```

**Implementation**: Create `app/templates/components/sort_headers.html` macro

## Phase 3: Search Enhancement (Tasks 8-10)

### Task 8: Faceted Search Backend
**Complexity**: 4
**Test Units**: 8
**Dependencies**: Tasks 1-3

**Tests to Write First**:
```python
async def test_search_with_query_only()
async def test_search_in_title_field()
async def test_search_in_content_field()
async def test_search_with_type_filter()
async def test_search_with_growth_filter()
async def test_search_calculates_facets()
async def test_search_facet_counts_accurate()
async def test_search_empty_query_shows_all()
```

**Implementation**: Create enhanced search route in `app/routers/search.py`

---

### Task 9: Faceted Search UI
**Complexity**: 3
**Test Units**: 6
**Dependencies**: Task 8

**Tests to Write First**:
```python
def test_search_ui_shows_facets()
def test_facet_shows_result_counts()
def test_facet_links_preserve_search_query()
def test_active_facets_highlighted()
def test_remove_facet_preserves_other_filters()
def test_facet_section_hidden_when_no_results()
```

**Implementation**: Create `app/templates/search.html` with facets

---

### Task 10: Search Field Targeting
**Complexity**: 2
**Test Units**: 5
**Dependencies**: Task 9

**Tests to Write First**:
```python
def test_search_field_dropdown_options()
def test_search_field_selection_preserved()
def test_search_field_affects_results()
def test_search_field_default_to_all()
def test_search_field_in_url_params()
```

**Implementation**: Add field targeting to search UI

## Phase 4: Progressive Enhancements (Tasks 11-13)

### Task 11: Quick Filter Pills
**Complexity**: 2
**Test Units**: 5
**Dependencies**: Tasks 4-7

**Tests to Write First**:
```python
def test_quick_pills_render_correctly()
def test_quick_pill_links_have_correct_params()
def test_quick_pill_active_state_styling()
def test_quick_pills_responsive_layout()
def test_custom_quick_pills_from_config()
```

**Implementation**: Create quick filter pills component

---

### Task 12: URL Share Button
**Complexity**: 1
**Test Units**: 4
**Dependencies**: Task 4

**Tests to Write First**:
```python
def test_share_button_renders()
def test_share_button_copies_current_url()
def test_share_button_shows_feedback()
def test_share_button_accessibility()
```

**Implementation**: Add share button component

---

### Task 13: State Reset Control
**Complexity**: 2
**Test Units**: 4
**Dependencies**: Tasks 4-7

**Tests to Write First**:
```python
def test_reset_button_shows_when_filters_active()
def test_reset_button_hidden_when_no_filters()
def test_reset_button_clears_all_params()
def test_reset_button_preserves_base_path()
```

**Implementation**: Add reset filters button

## Phase 5: Advanced Features (Tasks 14-15)

### Task 14: Saved Searches
**Complexity**: 5
**Test Units**: 10
**Dependencies**: Tasks 1-13

**Tests to Write First**:
```python
async def test_save_search_stores_params()
async def test_save_search_generates_unique_id()
async def test_load_saved_search_restores_state()
async def test_list_saved_searches()
async def test_delete_saved_search()
async def test_saved_search_with_custom_name()
async def test_saved_search_persistence()
async def test_saved_search_in_navigation()
async def test_duplicate_saved_search_handling()
async def test_saved_search_url_format()
```

**Implementation**: Create saved search system

---

### Task 15: Timeline Navigation
**Complexity**: 4
**Test Units**: 8
**Dependencies**: Tasks 1-3

**Tests to Write First**:
```python
async def test_timeline_by_year()
async def test_timeline_by_year_month()
async def test_timeline_with_content_type_filter()
async def test_timeline_navigation_controls()
async def test_timeline_empty_periods()
async def test_timeline_date_parsing()
async def test_timeline_performance()
async def test_timeline_ui_rendering()
```

**Implementation**: Create timeline navigation route and UI

## Testing Strategy

### Unit Test Coverage
- All service methods: 100%
- URL parameter parsing: 100%
- Filter logic: 100%
- Sort logic: 100%

### Integration Test Coverage
- Route + Service: Each route tested
- Template + HTMX: Key interactions tested
- End-to-end flows: Major user journeys

### Performance Testing
- Filter performance with 1000+ items
- URL parsing with complex parameters
- Template rendering with full state

## Risk Mitigation

### Identified Risks
1. **URL Length Limits**: Mitigate with parameter abbreviation
2. **Performance with Complex Filters**: Add caching layer
3. **Browser History Pollution**: Implement debouncing
4. **State Synchronization**: Single source of truth in URL

### Mitigation Strategies
- Implement parameter compression for long URLs
- Add query result caching with TTL
- Debounce HTMX requests on rapid changes
- Comprehensive error handling for malformed URLs

## Validation Checklist

### Phase 1 Complete When:
- [ ] URL parser handles all parameter types
- [ ] Filter service filters correctly
- [ ] Sort service sorts all fields

### Phase 2 Complete When:
- [ ] Home route supports all filters
- [ ] Filter bar fully functional
- [ ] Sort headers toggle correctly

### Phase 3 Complete When:
- [ ] Search supports facets
- [ ] Search UI shows refinements
- [ ] Field targeting works

### Phase 4 Complete When:
- [ ] Quick pills navigate correctly
- [ ] Share button copies URL
- [ ] Reset clears all filters

### Phase 5 Complete When:
- [ ] Saved searches persist
- [ ] Timeline navigation works
- [ ] All features integrated

## Success Metrics
- All 15 tasks completed with tests passing
- 100+ unit tests, all green
- URL state preserved across all interactions
- Browser back/forward navigation works
- Performance acceptable (<100ms filter operations)