# Pattern: Investigation-First Development
**Category**: Development Methodology
**Confidence**: High
**Validated**: 3+ instances

## Description
Always investigate existing infrastructure, dependencies, and implementations before adding new features or dependencies. This pattern prevents unnecessary work and reveals hidden capabilities.

## When to Apply
- Before implementing any new feature
- When a capability seems missing
- Before adding new dependencies
- When tests reveal unexpected behavior
- During feature gap analysis

## Implementation Steps
1. **Audit Existing Code**
   - Search for related functionality
   - Check for disabled or unconfigured features
   - Review test coverage for clues

2. **Map Dependencies**
   - Use `uv tree` to explore transitive dependencies
   - Check if needed libraries are already available
   - Review import statements in similar components

3. **Write Discovery Tests**
   - Create tests for expected behavior
   - Use test failures to understand actual state
   - Let tests guide investigation focus

4. **Check Configuration**
   - Review environment variables
   - Examine configuration files
   - Look for feature flags or toggles

## Evidence from Digital Garden

### Instance 1: Syntax Highlighting (Task 19)
- **Assumption**: Needed to add Pygments dependency
- **Discovery**: Pygments available via Rich transitive dependency
- **Actual Gap**: Only CSS styling was missing
- **Result**: Avoided unnecessary dependency, focused on real gap

### Instance 2: Error Pages (Task 22)
- **Assumption**: Might have partial error handling
- **Discovery**: Complete absence of error templates
- **Actual Gap**: No custom error pages at all
- **Result**: Clear implementation path identified

### Instance 3: Feature Completeness
- **Pattern**: Backend often complete, frontend incomplete
- **Evidence**: Multiple features had full backend but missing UI
- **Learning**: UI/UX gaps often mask complete functionality

## Benefits
- Prevents duplicate implementations
- Reduces technical debt
- Leverages existing infrastructure
- Saves development time
- Improves code consistency

## Anti-patterns to Avoid
- ❌ Assuming features don't exist without checking
- ❌ Adding dependencies without auditing current ones
- ❌ Implementing from scratch without investigation
- ❌ Ignoring test results that show existing functionality

## Related Patterns
- Test-Driven Discovery
- Dependency Audit Pattern
- CSS-Only Enhancement

## Tools and Commands
```bash
# Dependency investigation
uv tree                    # View dependency tree
uv pip list               # List all installed packages

# Code investigation
rg "pattern" --type py    # Search Python files
grep -r "feature" app/    # Search recursively

# Test investigation
pytest -k "feature" -v    # Run specific tests
pytest --collect-only     # List all tests
```

## Checklist
- [ ] Searched codebase for related functionality
- [ ] Audited current dependencies
- [ ] Wrote discovery tests
- [ ] Checked configuration options
- [ ] Reviewed similar implementations
- [ ] Documented actual vs perceived gaps