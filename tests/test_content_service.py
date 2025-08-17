"""
Test suite for ContentService class implementing IContentProvider interface.
Tests follow strict TDD principles and must fail initially.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Fixtures for test data
@pytest.fixture
def sample_content_with_frontmatter():
    """Sample markdown content with valid YAML frontmatter."""
    return """---
title: "Test Article"
created: "2024-03-14"
updated: "2024-03-15"
tags: [python, testing]
status: "Evergreen"
growth_stage: "evergreen"
---

# Test Article

This is test content with **markdown** formatting.

- List item 1
- List item 2

[Link text](https://example.com)
"""

@pytest.fixture
def sample_draft_content():
    """Sample draft content that should be filtered out."""
    return """---
title: "Draft Article"
created: "2024-03-14"
tags: [draft]
status: "draft"
---

This is draft content that should be filtered.
"""

@pytest.fixture
def invalid_growth_stage_content():
    """Sample content with invalid growth stage."""
    return """---
title: "Invalid Growth"
created: "2024-03-14"
growth_stage: "invalid_stage"
---

Content with invalid growth stage.
"""

@pytest.fixture
def malformed_yaml_content():
    """Sample content with malformed YAML frontmatter."""
    return """---
title: "Broken YAML"
created: [this is not valid yaml
tags: 
---

Content with broken frontmatter.
"""

@pytest.fixture
def content_without_frontmatter():
    """Sample markdown content without frontmatter."""
    return """# Article Without Frontmatter

This content has no YAML frontmatter at all.
"""

@pytest.fixture
def mock_content_dir(tmp_path):
    """Create a mock content directory structure."""
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    
    # Create subdirectories
    (content_dir / "notes").mkdir()
    (content_dir / "til").mkdir()
    (content_dir / "bookmarks").mkdir()
    
    return content_dir

@pytest.fixture
def mock_content_files(mock_content_dir, sample_content_with_frontmatter, sample_draft_content):
    """Create mock content files in the test directory."""
    # Create a published note
    note_path = mock_content_dir / "notes" / "test-article.md"
    note_path.write_text(sample_content_with_frontmatter)
    
    # Create a draft note
    draft_path = mock_content_dir / "notes" / "draft-article.md"
    draft_path.write_text(sample_draft_content)
    
    # Create a TIL post
    til_content = """---
title: "Python Tip"
created: "2024-03-13"
tags: [python, til]
status: "Budding"
---

Today I learned about Python decorators.
"""
    til_path = mock_content_dir / "til" / "python-tip.md"
    til_path.write_text(til_content)
    
    # Create a bookmark
    bookmark_content = """---
title: "Useful Resource"
created: "2024-03-12"
url: "https://example.com/resource"
tags: [resources]
status: "Evergreen"
---

A useful development resource.
"""
    bookmark_path = mock_content_dir / "bookmarks" / "useful-resource.md"
    bookmark_path.write_text(bookmark_content)
    
    return mock_content_dir


class TestContentServiceRequiredTests:
    """Test the 8 required behaviors specified in Task 6."""
    
    def test_content_service_implements_interface(self):
        """Test 1: Verify ContentService implements IContentProvider."""
        try:
            from app.services.content_service import ContentService
            from app.interfaces import IContentProvider
            
            # Verify ContentService is a subclass of IContentProvider
            assert issubclass(ContentService, IContentProvider), \
                "ContentService should implement IContentProvider interface"
            
            # Verify it can be instantiated
            service = ContentService()
            assert isinstance(service, IContentProvider), \
                "ContentService instance should be an IContentProvider"
                
        except ImportError as e:
            pytest.fail(f"ContentService should exist and be importable: {e}")
    
    def test_get_content_by_slug_returns_parsed_content(self, mock_content_files, sample_content_with_frontmatter):
        """Test 2: Test parsing markdown with frontmatter for valid slug."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService(content_dir=str(mock_content_files))
            
            # Test getting content by slug
            content = service.get_content_by_slug("notes", "test-article")
            
            assert content is not None, "Should return content for valid slug"
            assert content["title"] == "Test Article", "Should parse title from frontmatter"
            assert content["status"] == "Evergreen", "Should parse status"
            assert "python" in content["tags"], "Should parse tags"
            assert "html" in content, "Should include HTML content"
            assert "<strong>markdown</strong>" in content["html"], "Should convert markdown to HTML"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_get_content_by_slug_returns_none_for_missing(self, mock_content_dir):
        """Test 3: Test behavior when slug doesn't exist."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService(content_dir=str(mock_content_dir))
            
            # Test getting non-existent content
            content = service.get_content_by_slug("notes", "non-existent-slug")
            
            assert content is None, "Should return None for missing slug"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_get_all_content_returns_all_parsed_files(self, mock_content_files):
        """Test 4: Test discovery and parsing of all content files."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService(content_dir=str(mock_content_files))
            
            # Get all content
            all_content = service.get_all_content()
            
            assert isinstance(all_content, list), "Should return a list"
            assert len(all_content) > 0, "Should find content files"
            
            # Check that draft content is excluded by default
            titles = [item["title"] for item in all_content]
            assert "Draft Article" not in titles, "Should exclude draft content"
            assert "Test Article" in titles, "Should include published content"
            assert "Python Tip" in titles, "Should include TIL content"
            assert "Useful Resource" in titles, "Should include bookmark content"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_content_parsing_validates_growth_stage(self, mock_content_dir, invalid_growth_stage_content):
        """Test 5: Test that invalid growth stages raise ValidationError."""
        try:
            from app.services.content_service import ContentService
            from pydantic import ValidationError
            
            # Create a file with invalid growth stage
            invalid_path = mock_content_dir / "notes" / "invalid-growth.md"
            invalid_path.write_text(invalid_growth_stage_content)
            
            service = ContentService(content_dir=str(mock_content_dir))
            
            # This should raise ValidationError
            with pytest.raises(ValidationError) as exc_info:
                service.get_content_by_slug("notes", "invalid-growth")
            
            # Check that the error mentions the invalid growth stage
            error_str = str(exc_info.value)
            assert "growth_stage" in error_str or "invalid_stage" in error_str, \
                f"Validation error should mention invalid growth stage, got: {error_str}"
                
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_content_caching_works_correctly(self, mock_content_files):
        """Test 6: Test that repeated calls return cached results."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService(content_dir=str(mock_content_files))
            
            # First call - should read from disk
            with patch("builtins.open", mock_open(read_data="---\ntitle: Test\n---\nContent")):
                first_result = service.get_content_by_slug("notes", "test-article")
            
            # Second call - should use cache
            with patch("builtins.open", mock_open(read_data="---\ntitle: Test\n---\nContent")) as mock_file:
                second_result = service.get_content_by_slug("notes", "test-article")
                second_call_count = mock_file.call_count
            
            # Results should be the same
            assert first_result == second_result, "Cached result should match original"
            
            # File should not be read again (or read less frequently)
            assert second_call_count == 0, "Should use cached result, not read file again"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_content_filters_by_status_published_only(self, mock_content_files):
        """Test 7: Test that draft content is filtered out."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService(content_dir=str(mock_content_files))
            
            # Get content from notes directory
            notes_content = service.get_content("notes")
            
            assert isinstance(notes_content, dict), "Should return dict with content"
            assert "content" in notes_content, "Should have content key"
            
            content_list = notes_content["content"]
            
            # Check that draft is filtered out
            statuses = [item.get("status") for item in content_list if "status" in item]
            assert "draft" not in statuses, "Should filter out draft content"
            
            # Check that published content is included
            titles = [item.get("title") for item in content_list]
            assert "Test Article" in titles, "Should include published content"
            assert "Draft Article" not in titles, "Should exclude draft content"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_markdown_to_html_conversion_works(self):
        """Test 8: Test markdown parsing with Python-markdown."""
        try:
            from app.services.content_service import ContentService
            
            service = ContentService()
            
            # Test markdown conversion
            markdown_text = """# Heading 1

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2

[Link text](https://example.com)

```python
def hello():
    print("Hello, World!")
```
"""
            
            # Use the render_markdown method
            result = service.render_markdown(markdown_text)
            
            assert "html" in result, "Should return HTML"
            html = result["html"]
            
            # Check HTML conversion (allowing for id attributes)
            assert "<h1" in html, "Should convert headings"
            assert "Heading 1</h1>" in html, "Should have heading content"
            assert "<strong>bold</strong>" in html, "Should convert bold text"
            assert "<em>italic</em>" in html, "Should convert italic text"
            assert "<ul>" in html, "Should convert lists"
            assert "<li>List item 1</li>" in html, "Should convert list items"
            assert '<a href="https://example.com">' in html, "Should convert links"
            
        except ImportError:
            pytest.fail("ContentService should be importable")


class TestContentServiceInterfaceMethods:
    """Test that all IContentProvider interface methods are implemented."""
    
    def test_all_interface_methods_exist(self):
        """Test that ContentService has all required interface methods."""
        try:
            from app.services.content_service import ContentService
            from app.interfaces import IContentProvider
            import inspect
            
            # Get all abstract methods from interface
            interface_methods = [
                method for method in dir(IContentProvider)
                if not method.startswith('_') and callable(getattr(IContentProvider, method))
            ]
            
            # Verify ContentService has all methods
            service = ContentService()
            for method_name in interface_methods:
                assert hasattr(service, method_name), \
                    f"ContentService should have method: {method_name}"
                assert callable(getattr(service, method_name)), \
                    f"{method_name} should be callable"
                    
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_async_methods_are_async(self):
        """Test that async interface methods are implemented as async."""
        try:
            from app.services.content_service import ContentService
            import asyncio
            import inspect
            
            service = ContentService()
            
            # Check specific async methods
            async_methods = ["get_mixed_content", "get_homepage_sections"]
            
            for method_name in async_methods:
                method = getattr(service, method_name)
                assert asyncio.iscoroutinefunction(method) or inspect.iscoroutinefunction(method), \
                    f"{method_name} should be async"
                    
        except ImportError:
            pytest.fail("ContentService should be importable")


class TestContentServiceEdgeCases:
    """Test edge cases and error handling."""
    
    def test_handles_malformed_yaml_gracefully(self, mock_content_dir, malformed_yaml_content):
        """Test handling of malformed YAML frontmatter."""
        try:
            from app.services.content_service import ContentService
            
            # Create file with malformed YAML
            malformed_path = mock_content_dir / "notes" / "malformed.md"
            malformed_path.write_text(malformed_yaml_content)
            
            service = ContentService(content_dir=str(mock_content_dir))
            
            # Should handle gracefully without crashing
            content = service.get_content_by_slug("notes", "malformed")
            
            # Should return content with defaults when YAML is malformed
            assert content is not None, "Should return content even with malformed YAML"
            assert "html" in content, "Should still convert markdown to HTML"
            assert content.get("title"), "Should have a default title"
            assert content.get("status") == "Evergreen", "Should have default status"
                
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_handles_content_without_frontmatter(self, mock_content_dir, content_without_frontmatter):
        """Test handling of content without YAML frontmatter."""
        try:
            from app.services.content_service import ContentService
            
            # Create file without frontmatter
            no_fm_path = mock_content_dir / "notes" / "no-frontmatter.md"
            no_fm_path.write_text(content_without_frontmatter)
            
            service = ContentService(content_dir=str(mock_content_dir))
            
            # Should handle gracefully
            content = service.get_content_by_slug("notes", "no-frontmatter")
            
            # Could return content with defaults or None
            if content:
                assert "html" in content, "Should still convert markdown to HTML"
                
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_handles_empty_directory(self, mock_content_dir):
        """Test handling of empty content directories."""
        try:
            from app.services.content_service import ContentService
            
            # Create empty directory
            empty_dir = mock_content_dir / "empty"
            empty_dir.mkdir()
            
            service = ContentService(content_dir=str(mock_content_dir))
            
            # Should handle empty directory gracefully
            content = service.get_content("empty")
            
            assert content is not None, "Should return result for empty directory"
            assert "content" in content, "Should have content key"
            assert len(content["content"]) == 0, "Should return empty list for empty directory"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_handles_nonexistent_directory(self):
        """Test handling of non-existent content directory."""
        try:
            from app.services.content_service import ContentService
            
            # Try to create service with non-existent directory
            service = ContentService(content_dir="/non/existent/path")
            
            # Should handle gracefully
            content = service.get_all_content()
            
            assert isinstance(content, list), "Should return empty list for missing directory"
            assert len(content) == 0, "Should return empty list when directory doesn't exist"
            
        except ImportError:
            pytest.fail("ContentService should be importable")


class TestContentServiceConfiguration:
    """Test ContentService configuration and initialization."""
    
    def test_can_configure_content_directory(self, tmp_path):
        """Test that content directory can be configured."""
        try:
            from app.services.content_service import ContentService
            
            custom_dir = tmp_path / "custom_content"
            custom_dir.mkdir()
            
            service = ContentService(content_dir=str(custom_dir))
            
            # Should use custom directory
            assert service._content_dir == Path(custom_dir) or \
                   str(service._content_dir) == str(custom_dir), \
                "Should use configured content directory"
                
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_can_configure_cache_ttl(self):
        """Test that cache TTL can be configured."""
        try:
            from app.services.content_service import ContentService
            
            # Create with custom TTL
            service = ContentService(cache_ttl=600)
            
            # Should use custom TTL (this would need internal access to verify)
            # For now, just verify it accepts the parameter
            assert service is not None, "Should accept cache_ttl parameter"
            
        except ImportError:
            pytest.fail("ContentService should be importable")
    
    def test_default_configuration_works(self):
        """Test that ContentService works with default configuration."""
        try:
            from app.services.content_service import ContentService
            
            # Should work with no parameters
            service = ContentService()
            
            assert service is not None, "Should work with default configuration"
            
            # Should have default methods available
            assert hasattr(service, "get_all_content"), "Should have interface methods"
            
        except ImportError:
            pytest.fail("ContentService should be importable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])