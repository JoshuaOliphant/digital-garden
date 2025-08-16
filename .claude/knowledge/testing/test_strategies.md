# Testing Strategies - Digital Garden

## Test Organization

### Unit Tests
- Model validation (`test_models.py`)
- Utility functions (`test_utils.py`)
- Content parsing (`test_markdown.py`)

### Integration Tests
- API endpoints (`test_main.py`)
- Content manager (`test_content_manager.py`)
- Template rendering (`test_templates.py`)

### End-to-End Tests
- User flows (`test_e2e.py`)
- Panel navigation (`test_sliding_panel_ui.py`)
- Content discovery (`test_content_discovery.py`)

## Common Test Patterns

### Async Test Pattern
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_endpoint(client: AsyncClient):
    response = await client.get("/api/content")
    assert response.status_code == 200
```

### Model Validation Pattern
```python
def test_content_model_validation():
    with pytest.raises(ValidationError):
        Content(title="")  # Missing required field
    
    content = Content(title="Test", created="2024-01-01")
    assert content.title == "Test"
```

### Pagination Test Pattern
```python
@pytest.mark.parametrize("page,expected_count", [
    (1, 10),
    (2, 10),
    (100, 0),  # Beyond last page
])
def test_pagination(page, expected_count):
    result = get_paginated_content(page=page)
    assert len(result.items) == expected_count
```

### Mock External API Pattern
```python
from unittest.mock import patch, Mock

@patch('httpx.get')
def test_github_stars(mock_get):
    mock_get.return_value = Mock(
        json=lambda: {"stargazers_count": 42}
    )
    stars = get_github_stars("owner/repo")
    assert stars == 42
```

## Test Data Management

### Fixtures
```python
@pytest.fixture
def sample_content():
    return {
        "title": "Test Note",
        "created": "2024-01-01",
        "tags": ["test", "sample"],
        "content": "Test content"
    }

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### Test Data Files
```
tests/
├── fixtures/
│   ├── sample_note.md
│   ├── invalid_frontmatter.md
│   └── large_content.md
```

## Coverage Goals

### Target Coverage
- Overall: 80%
- Critical paths: 95%
- Models: 100%
- Utilities: 90%

### Coverage Commands
```bash
# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html

# Check specific module
pytest --cov=app.models tests/test_models.py
```

## Performance Testing

### Load Testing Pattern
```python
import asyncio
import time

async def test_concurrent_requests():
    start = time.time()
    tasks = [client.get("/api/content") for _ in range(100)]
    responses = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    assert all(r.status_code == 200 for r in responses)
    assert duration < 5.0  # Should handle 100 requests in 5s
```

### Cache Testing
```python
def test_cache_hit_rate():
    # First call - cache miss
    result1 = get_cached_content()
    
    # Second call - cache hit
    result2 = get_cached_content()
    
    assert result1 == result2
    assert cache_hits() > 0
```

## Common Test Issues & Solutions

### Issue: Async fixture not working
```python
# Wrong
@pytest.fixture
async def data():
    return await fetch_data()

# Correct
@pytest.fixture
async def data():
    result = await fetch_data()
    return result
```

### Issue: File system tests failing
```python
# Use tmp_path fixture
def test_file_operations(tmp_path):
    test_file = tmp_path / "test.md"
    test_file.write_text("content")
    assert test_file.exists()
```

### Issue: Time-dependent tests
```python
from freezegun import freeze_time

@freeze_time("2024-01-01")
def test_date_handling():
    content = create_content()
    assert content.created == "2024-01-01"
```

## CI/CD Testing

### GitHub Actions
```yaml
- name: Run tests
  run: |
    uv sync
    uv run pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: uv run pytest
      language: system
      pass_filenames: false
      always_run: true
```