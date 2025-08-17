"""
Test suite for BacklinkService implementation.

Tests the discovery and management of content relationships through internal links.
Follows TDD principles with comprehensive test coverage.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Set
from datetime import datetime, timedelta

from app.interfaces import IBacklinkService, IContentProvider
from app.services.backlink_service import BacklinkService
from app.models import BaseContent


class TestBacklinkService:
    """Test suite for BacklinkService implementation."""

    @pytest.fixture
    def mock_content_provider(self):
        """Mock content provider for dependency injection."""
        mock = Mock(spec=IContentProvider)
        return mock

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return [
            {
                "slug": "note1",
                "title": "First Note",
                "content": "This is a link to [another note](notes/note2.md) and [[wiki-link]].",
                "file_path": "app/content/notes/note1.md"
            },
            {
                "slug": "note2",
                "title": "Second Note", 
                "content": "Reference back to [first note](notes/note1.md).",
                "file_path": "app/content/notes/note2.md"
            },
            {
                "slug": "note3",
                "title": "Third Note",
                "content": "Links to [note1](notes/note1.md) and mentions [[wiki-link]].",
                "file_path": "app/content/notes/note3.md"
            }
        ]

    @pytest.fixture
    def backlink_service(self, mock_content_provider):
        """BacklinkService instance for testing."""
        return BacklinkService(mock_content_provider)

    def test_extract_internal_links_markdown_format(self, backlink_service):
        """Test extraction of markdown-style internal links."""
        content = "Check out [this note](notes/example.md) and [another](../other.md)"
        content_path = "app/content/notes/test.md"
        
        links = backlink_service.extract_internal_links(content, content_path)
        
        assert "example" in links
        assert "other" in links
        assert len(links) == 2

    def test_extract_internal_links_wiki_format(self, backlink_service):
        """Test extraction of wiki-style internal links."""
        content = "See [[wiki-link]] and [[another page]] for details."
        content_path = "app/content/notes/test.md"
        
        links = backlink_service.extract_internal_links(content, content_path)
        
        assert "wiki-link" in links
        assert "another-page" in links
        assert len(links) == 2

    def test_extract_internal_links_mixed_formats(self, backlink_service):
        """Test extraction of mixed link formats."""
        content = """
        Markdown link: [example](notes/test.md)
        Wiki link: [[wiki-style]]
        External link: [google](https://google.com)
        Relative link: [local](./local.md)
        """
        content_path = "app/content/notes/test.md"
        
        links = backlink_service.extract_internal_links(content, content_path)
        
        # Should include internal links but not external
        assert "test" in links
        assert "wiki-style" in links  
        assert "local" in links
        assert len(links) == 3

    def test_extract_internal_links_no_links(self, backlink_service):
        """Test content with no internal links."""
        content = "This is just plain text with no links."
        content_path = "app/content/notes/test.md"
        
        links = backlink_service.extract_internal_links(content, content_path)
        
        assert len(links) == 0

    def test_get_backlinks_finds_references(self, backlink_service, mock_content_provider):
        """Test discovery of backlinks to target content."""
        # Mock content provider to return sample content
        mock_content_provider.get_all_content.return_value = [
            {"slug": "note1", "title": "Note 1", "content": "Link to [target](notes/target.md)", "file_path": "notes/note1.md"},
            {"slug": "note2", "title": "Note 2", "content": "Reference [[target]] here", "file_path": "notes/note2.md"},
            {"slug": "note3", "title": "Note 3", "content": "No links to target content", "file_path": "notes/note3.md"},
            {"slug": "target", "title": "Target", "content": "This is the target content", "file_path": "notes/target.md"}
        ]
        
        backlinks = backlink_service.get_backlinks("target")
        
        # Should find 2 backlinks
        assert len(backlinks) == 2
        
        # Check structure of returned backlinks
        source_slugs = [bl['source_slug'] for bl in backlinks]
        assert "note1" in source_slugs
        assert "note2" in source_slugs
        assert "note3" not in source_slugs
        assert "target" not in source_slugs

    def test_get_backlinks_no_references(self, backlink_service, mock_content_provider):
        """Test discovery when no backlinks exist."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "note1", "title": "Note 1", "content": "No links here", "file_path": "notes/note1.md"},
            {"slug": "target", "title": "Target", "content": "Target content", "file_path": "notes/target.md"}
        ]
        
        backlinks = backlink_service.get_backlinks("target")
        
        assert backlinks == []

    def test_get_forward_links_finds_outgoing_links(self, backlink_service, mock_content_provider):
        """Test finding forward links from source content."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "source", "title": "Source", "content": "Link to [target1](notes/target1.md) and [[target2]]", "file_path": "notes/source.md"},
            {"slug": "target1", "title": "Target 1", "content": "Target 1 content", "file_path": "notes/target1.md"},
            {"slug": "target2", "title": "Target 2", "content": "Target 2 content", "file_path": "notes/target2.md"}
        ]
        
        forward_links = backlink_service.get_forward_links("source")
        
        assert len(forward_links) == 2
        target_slugs = [fl['target_slug'] for fl in forward_links]
        assert "target1" in target_slugs
        assert "target2" in target_slugs

    def test_get_forward_links_no_outgoing_links(self, backlink_service, mock_content_provider):
        """Test forward links when content has no outgoing links."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "source", "title": "Source", "content": "No links in this content", "file_path": "notes/source.md"}
        ]
        
        forward_links = backlink_service.get_forward_links("source")
        
        assert forward_links == []

    def test_build_link_graph_complete(self, backlink_service, mock_content_provider):
        """Test building complete link graph."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "note1", "title": "Note 1", "content": "Link to [note2](notes/note2.md)", "file_path": "notes/note1.md"},
            {"slug": "note2", "title": "Note 2", "content": "Link to [note3](notes/note3.md)", "file_path": "notes/note2.md"},
            {"slug": "note3", "title": "Note 3", "content": "Link back to [note1](notes/note1.md)", "file_path": "notes/note3.md"}
        ]
        
        graph = backlink_service.build_link_graph()
        
        assert "note1" in graph
        assert "note2" in graph["note1"]
        assert "note3" in graph["note2"] 
        assert "note1" in graph["note3"]
        assert len(graph) == 3

    def test_build_link_graph_isolated_nodes(self, backlink_service, mock_content_provider):
        """Test graph with isolated nodes."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "connected1", "title": "Connected 1", "content": "Link to [connected2](notes/connected2.md)", "file_path": "notes/connected1.md"},
            {"slug": "connected2", "title": "Connected 2", "content": "Connected content", "file_path": "notes/connected2.md"},
            {"slug": "isolated", "title": "Isolated", "content": "No links anywhere", "file_path": "notes/isolated.md"}
        ]
        
        graph = backlink_service.build_link_graph()
        
        assert "connected1" in graph
        assert "connected2" in graph["connected1"]
        assert "connected2" in graph
        assert "isolated" in graph
        assert len(graph["isolated"]) == 0

    def test_validate_links_finds_broken_links(self, backlink_service, mock_content_provider):
        """Test link validation finds broken links."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "source", "title": "Source", "content": "Link to [missing](notes/missing.md)", "file_path": "notes/source.md"},
            {"slug": "source2", "title": "Source 2", "content": "Link to [existing](notes/existing.md)", "file_path": "notes/source2.md"},
            {"slug": "existing", "title": "Existing", "content": "Valid target", "file_path": "notes/existing.md"}
        ]
        
        broken_links = backlink_service.validate_links()
        
        assert len(broken_links) == 1
        assert broken_links[0]['source_slug'] == "source"
        assert broken_links[0]['broken_link'] == "missing"

    def test_validate_links_no_broken_links(self, backlink_service, mock_content_provider):
        """Test link validation when all links are valid."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "source", "title": "Source", "content": "Link to [target](notes/target.md)", "file_path": "notes/source.md"},
            {"slug": "target", "title": "Target", "content": "Valid target", "file_path": "notes/target.md"}
        ]
        
        broken_links = backlink_service.validate_links()
        
        assert broken_links == []

    def test_get_orphaned_content_finds_orphans(self, backlink_service, mock_content_provider):
        """Test finding orphaned content."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "connected1", "title": "Connected 1", "content": "Link to [connected2](notes/connected2.md)", "file_path": "notes/connected1.md"},
            {"slug": "connected2", "title": "Connected 2", "content": "Link to [connected1](notes/connected1.md)", "file_path": "notes/connected2.md"},
            {"slug": "orphan", "title": "Orphan", "content": "No links in or out", "file_path": "notes/orphan.md"}
        ]
        
        orphans = backlink_service.get_orphaned_content()
        
        assert "orphan" in orphans
        assert "connected1" not in orphans
        assert "connected2" not in orphans

    def test_get_orphaned_content_no_orphans(self, backlink_service, mock_content_provider):
        """Test when no orphaned content exists."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "note1", "title": "Note 1", "content": "Link to [note2](notes/note2.md)", "file_path": "notes/note1.md"},
            {"slug": "note2", "title": "Note 2", "content": "Link to [note1](notes/note1.md)", "file_path": "notes/note2.md"}
        ]
        
        orphans = backlink_service.get_orphaned_content()
        
        assert orphans == []

    def test_refresh_cache_clears_data(self, backlink_service, mock_content_provider):
        """Test cache refresh clears cached data."""
        # Pre-populate cache
        backlink_service._backlinks_cache = {"target": [{"source_slug": "old"}]}
        backlink_service._link_graph_cache = {"old": ["data"]}
        backlink_service._cache_time = datetime.now() - timedelta(hours=1)
        
        backlink_service.refresh_cache()
        
        assert len(backlink_service._backlinks_cache) == 0
        assert backlink_service._link_graph_cache is None
        assert backlink_service._cache_time is None

    def test_cache_performance_caching_works(self, backlink_service, mock_content_provider):
        """Test that caching provides performance benefits."""
        mock_content_provider.get_all_content.return_value = [
            {"slug": "target", "title": "Target", "content": "Target content", "file_path": "notes/target.md"}
        ]
        
        # First call should populate cache
        backlinks1 = backlink_service.get_backlinks("target")
        
        # Second call should use cache (won't call get_all_content again)
        backlinks2 = backlink_service.get_backlinks("target")
        
        # Should have been called only once due to caching
        assert mock_content_provider.get_all_content.call_count == 1
        assert backlinks1 == backlinks2

    def test_error_handling_invalid_content(self, backlink_service, mock_content_provider):
        """Test error handling for invalid content."""
        mock_content_provider.get_all_content.side_effect = Exception("Content provider error")
        
        # Should handle errors gracefully
        backlinks = backlink_service.get_backlinks("target")
        assert backlinks == []
        
        forward_links = backlink_service.get_forward_links("source")
        assert forward_links == []
        
        graph = backlink_service.build_link_graph()
        assert graph == {}

    def test_normalize_link_target_removes_extension(self, backlink_service):
        """Test link target normalization removes .md extension."""
        normalized = backlink_service._normalize_link_target("notes/example.md", "")
        assert normalized == "example"

    def test_normalize_wiki_link_converts_spaces(self, backlink_service):
        """Test wiki link normalization converts spaces to hyphens."""
        normalized = backlink_service._normalize_wiki_link("My Page Title")
        assert normalized == "my-page-title"

    def test_link_matches_target_various_formats(self, backlink_service):
        """Test link matching with various formats."""
        # Direct match
        assert backlink_service._link_matches_target("example", "example")
        
        # Case insensitive
        assert backlink_service._link_matches_target("Example", "example")
        
        # Wiki style
        assert backlink_service._link_matches_target("my page", "my-page")

    def test_is_internal_link_correctly_identifies(self, backlink_service):
        """Test internal link identification."""
        # Internal links
        assert backlink_service._is_internal_link("notes/example.md")
        assert backlink_service._is_internal_link("./relative.md")
        assert backlink_service._is_internal_link("../parent.md")
        
        # External links
        assert not backlink_service._is_internal_link("https://example.com")
        assert not backlink_service._is_internal_link("http://test.org")

    def test_extract_link_context_finds_context(self, backlink_service):
        """Test extraction of link context."""
        content = "This is a line with a [link](target.md) in it.\nAnother line."
        context = backlink_service._extract_link_context(content, "target", "target")
        
        assert "link" in context
        assert len(context) <= 100  # Should be truncated