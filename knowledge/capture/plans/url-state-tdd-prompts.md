# TDD Implementation Prompts for URL State Management

## Task 1: URL Parameter Parser Service

```text
Think carefully about implementing a URL parameter parser service using strict TDD principles.

**Previous Context**: 
Digital Garden application uses FastAPI and serves content with basic routing. No URL state management exists yet.

**Your Task**:
Create a URLStateParser service that parses query parameters and returns structured filter state.

**Tests to Write FIRST** (must fail initially):
1. test_parse_empty_params_returns_defaults() - empty params should return sensible defaults
2. test_parse_types_comma_separated() - "types=notes,til" should parse to ["notes", "til"]  
3. test_parse_tags_comma_separated() - "tags=python,htmx" should parse to ["python", "htmx"]
4. test_parse_growth_stages_comma_separated() - "growth=seedling,evergreen" should parse
5. test_parse_sort_field_with_validation() - only allow valid sort fields
6. test_parse_order_direction_validation() - only "asc" or "desc" allowed
7. test_parse_page_number_validation() - must be positive integer
8. test_parse_invalid_params_returns_defaults() - malformed params handled gracefully

**Implementation Approach**:
- Create app/services/url_state.py
- Use pydantic BaseModel for validation
- Return dataclass or TypedDict with parsed state
- Consider using FastAPI's Query parameter validation

**Integration Requirements**:
1. Must work with FastAPI Query parameters
2. Should return type-safe structured data
3. Handle URL encoding/decoding properly

**Success Validation**:
- All 8 tests pass
- Service handles edge cases gracefully
- Type hints comprehensive
- No external dependencies beyond FastAPI/pydantic

Begin by writing the failing tests in tests/test_url_state.py
```

## Task 2: Filter Service Core

```text
Think carefully about implementing content filtering using strict TDD principles.

**Previous Context**:
URLStateParser from Task 1 provides parsed filter criteria. ContentService exists and returns all content.

**Your Task**:
Create ContentFilterService that filters content based on multiple criteria.

**Tests to Write FIRST** (must fail initially):
1. test_filter_by_single_content_type() - filter to show only "notes"
2. test_filter_by_multiple_content_types() - filter for ["notes", "til"]
3. test_filter_by_single_tag() - show only content with "python" tag
4. test_filter_by_multiple_tags_intersection() - content must have ALL specified tags
5. test_filter_by_growth_stage() - filter by growth stage like "evergreen"
6. test_filter_by_combined_criteria() - type AND tags AND growth
7. test_filter_excludes_drafts_by_default() - never show draft status unless explicit
8. test_filter_with_empty_criteria_returns_all() - no filters = all content
9. test_filter_preserves_content_structure() - doesn't modify content objects
10. test_filter_performance_with_large_dataset() - <10ms for 1000 items

**Implementation Approach**:
- Create app/services/content_filter.py
- Use functional approach with filter predicates
- Compose filters for multiple criteria
- Optimize with early returns

**Integration Requirements**:
1. Accept content list from ContentService
2. Accept filter criteria from URLStateParser
3. Return filtered list maintaining order
4. Work with existing content dictionary structure

**Success Validation**:
- All 10 tests pass
- Performance test meets threshold
- Works with real content structure
- Handles None/empty values in content

Begin by writing the failing tests in tests/test_content_filter.py
```

## Task 3: Sort Service

```text
Think carefully about implementing content sorting using strict TDD principles.

**Previous Context**:
ContentFilterService from Task 2 returns filtered content. Need to sort the results.

**Your Task**:
Extend ContentFilterService with sorting capabilities.

**Tests to Write FIRST** (must fail initially):
1. test_sort_by_created_date_desc() - newest first (default)
2. test_sort_by_created_date_asc() - oldest first
3. test_sort_by_updated_date() - sort by updated field
4. test_sort_by_title_alphabetical() - A-Z sorting
5. test_sort_with_null_values() - handle missing dates/fields
6. test_sort_maintains_stable_order() - equal values preserve original order

**Implementation Approach**:
- Add sort methods to ContentFilterService
- Use key functions for sorting
- Handle None values consistently
- Consider secondary sort keys

**Integration Requirements**:
1. Chain with filter operations
2. Accept sort field and direction
3. Validate sort fields against allowed list
4. Default to created desc if not specified

**Success Validation**:
- All 6 tests pass
- Sorting is stable
- Handles all content types
- Performance acceptable

Begin by adding failing tests to tests/test_content_filter.py
```

## Task 4: Enhanced Home Route with Filters

```text
Think carefully about enhancing the home route with URL state using strict TDD principles.

**Previous Context**:
Services from Tasks 1-3 ready. Current home route shows all content without filtering.

**Your Task**:
Update home route to accept and process URL parameters for filtering/sorting.

**Tests to Write FIRST** (must fail initially):
1. test_home_route_without_params_shows_all() - default behavior preserved
2. test_home_route_with_type_filter() - /?types=notes filters correctly
3. test_home_route_with_tag_filter() - /?tags=python works
4. test_home_route_with_growth_filter() - /?growth=evergreen filters
5. test_home_route_with_sort_params() - /?sort=updated&order=asc sorts
6. test_home_route_preserves_state_in_template() - state passed to template
7. test_home_route_handles_invalid_params() - graceful error handling
8. test_home_route_pagination_preserves_filters() - page changes keep filters

**Implementation Approach**:
- Update app/routers/main.py home route
- Use FastAPI Query parameters
- Inject URLStateParser and ContentFilterService
- Pass state to template context

**Integration Requirements**:
1. Preserve existing route functionality
2. Add Query parameters for all filters
3. Pass current_filters to template
4. Maintain HTMX compatibility

**Success Validation**:
- All 8 tests pass
- No regression in existing functionality
- Template receives filter state
- URLs are human-readable

Begin by writing failing tests in tests/test_routes_with_filters.py
```

## Task 5: Filter Bar Template Component

```text
Think carefully about creating a filter bar UI component using strict TDD principles.

**Previous Context**:
Route from Task 4 passes filter state to templates. Need UI for filter controls.

**Your Task**:
Create reusable filter bar template macro with HTMX integration.

**Tests to Write FIRST** (must fail initially):
1. test_filter_bar_renders_with_no_filters() - default state rendering
2. test_filter_bar_shows_active_type_filters() - checkboxes reflect state
3. test_filter_bar_shows_active_tag_filters() - selected tags highlighted
4. test_filter_bar_generates_correct_htmx_attributes() - hx-get, hx-target correct
5. test_filter_bar_preserves_hidden_state_fields() - other params preserved
6. test_filter_bar_shows_filter_count_badge() - "3 filters active"
7. test_filter_bar_responsive_layout() - mobile-friendly

**Implementation Approach**:
- Create app/templates/components/filter_bar.html
- Use Jinja2 macro with parameters
- Generate HTMX attributes dynamically
- Include hidden fields for state preservation

**Integration Requirements**:
1. Import as macro in base templates
2. Accept current_filters dictionary
3. Use existing Tailwind classes
4. Follow garden UI patterns

**Success Validation**:
- All 7 tests pass (use template rendering tests)
- HTMX attributes correct
- Responsive on mobile
- Accessible markup

Begin by writing template tests in tests/test_filter_templates.py
```

## Tasks 6-15: Additional Prompts

```text
[Prompts for Tasks 6-15 follow the same structure]

Task 6: HTMX State Preservation
- Focus on hx-push-url, hx-params="*", hx-include
- Test URL updates and form serialization

Task 7: Smart Sort Headers  
- Clickable headers that toggle sort direction
- Preserve all other filters when sorting

Task 8: Faceted Search Backend
- Calculate facets from search results
- Support field-specific searching

Task 9: Faceted Search UI
- Display facets with counts
- Allow refinement within results

Task 10: Search Field Targeting
- Dropdown for title/content/tags search
- Preserve selection in URL

Task 11: Quick Filter Pills
- Predefined filter combinations
- One-click common views

Task 12: URL Share Button
- Copy current URL to clipboard
- Visual feedback on copy

Task 13: State Reset Control
- Clear all filters button
- Only show when filters active

Task 14: Saved Searches
- Persist filter combinations
- User-defined names
- Backend storage

Task 15: Timeline Navigation
- Browse by year/month
- Calendar-style navigation
- Combine with other filters
```

## Usage Instructions

1. **Start with Task 1**: Foundation must be solid
2. **Write tests first**: Never write implementation before tests
3. **Run tests to see failure**: Confirm tests fail for the right reason
4. **Implement minimally**: Just enough to make tests pass
5. **Refactor if needed**: Clean up while keeping tests green
6. **Integrate**: Connect to existing system
7. **Document**: Update knowledge base with patterns learned

## Success Metrics

Each task is complete when:
- [ ] All specified tests written and failing initially
- [ ] Implementation makes all tests pass
- [ ] No regression in existing tests
- [ ] Code follows project patterns
- [ ] Integration verified with manual testing
- [ ] Knowledge captured for future reference

## Common Pitfalls to Avoid

1. **Writing implementation before tests** - Always test first
2. **Tests that don't fail initially** - Verify red before green
3. **Over-engineering** - Implement only what tests require
4. **Skipping integration** - Each task must connect to system
5. **Missing edge cases** - Think about nulls, empties, errors
6. **Ignoring performance** - Test with realistic data volumes
7. **Breaking existing features** - Run full test suite regularly