"""
Test suite for ContentManager logging functionality.
These tests verify logging of content operations, cache performance, and API integrations.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest

from app.main import ContentManager


class TestContentManagerLogging:
    """Test logging integration in ContentManager."""

    @pytest.fixture
    def content_manager(self, tmp_path):
        """Create ContentManager instance with test content directory."""
        # Create test content structure
        content_dir = tmp_path / "app" / "content"
        content_dir.mkdir(parents=True)
        
        # Create test content files
        notes_dir = content_dir / "notes"
        notes_dir.mkdir()
        
        test_note = notes_dir / "test-note.md"
        test_note.write_text("""---
title: Test Note
created: 2024-01-01
tags: [test, logging]
---

This is test content.
""")
        
        # Patch the content directory path
        with patch("app.main.Path") as mock_path:
            mock_path.return_value = content_dir
            manager = ContentManager()
            manager.content_dir = content_dir
            return manager

    def test_content_manager_has_logger(self, content_manager):
        """Test that ContentManager has a logger instance."""
        assert hasattr(content_manager, "logger")
        assert content_manager.logger is not None
        
        # Logger should have standard methods
        assert hasattr(content_manager.logger, "info")
        assert hasattr(content_manager.logger, "error")
        assert hasattr(content_manager.logger, "debug")
        assert hasattr(content_manager.logger, "warning")

    def test_content_manager_logs_initialization(self):
        """Test that ContentManager logs its initialization."""
        with patch("app.main.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            manager = ContentManager()
            
            # Should get logger with component name
            mock_get_logger.assert_called_with("ContentManager")
            
            # Should log initialization
            mock_logger.info.assert_called()
            calls = mock_logger.info.call_args_list
            assert any("initialized" in str(call).lower() for call in calls)

    def test_content_discovery_logging(self, content_manager):
        """Test logging during content discovery."""
        with patch.object(content_manager, "logger") as mock_logger:
            # Trigger content discovery
            content = content_manager.get_all_content()
            
            # Should log discovery process
            mock_logger.info.assert_called()
            calls = mock_logger.info.call_args_list
            
            # Should log content discovery start
            assert any("discovering" in str(call).lower() or "loading" in str(call).lower() 
                      for call in calls)
            
            # Should log content count
            assert any("found" in str(call).lower() or "loaded" in str(call).lower() 
                      for call in calls)

    def test_cache_hit_logging(self, content_manager):
        """Test logging of cache hits."""
        with patch.object(content_manager, "logger") as mock_logger:
            # First call - cache miss
            content1 = content_manager.get_all_content()
            
            # Second call - should be cache hit
            content2 = content_manager.get_all_content()
            
            # Should log cache hit
            calls = mock_logger.debug.call_args_list
            assert any("cache hit" in str(call).lower() for call in calls)

    def test_cache_miss_logging(self, content_manager):
        """Test logging of cache misses."""
        with patch.object(content_manager, "logger") as mock_logger:
            # Clear cache first
            content_manager._cache_clear()
            
            # This should be a cache miss
            content = content_manager.get_all_content()
            
            # Should log cache miss
            calls = mock_logger.debug.call_args_list
            assert any("cache miss" in str(call).lower() for call in calls)

    def test_content_parsing_error_logging(self, content_manager, tmp_path):
        """Test logging of content parsing errors."""
        # Create invalid content file
        invalid_file = tmp_path / "app" / "content" / "notes" / "invalid.md"
        invalid_file.parent.mkdir(parents=True, exist_ok=True)
        invalid_file.write_text("Invalid YAML frontmatter\n---\nContent")
        
        with patch.object(content_manager, "logger") as mock_logger:
            # Try to parse invalid content
            content = content_manager.parse_markdown_with_frontmatter(
                invalid_file.read_text(),
                "notes",
                "invalid"
            )
            
            # Should log parsing error
            mock_logger.error.assert_called()
            error_calls = mock_logger.error.call_args_list
            assert any("parsing" in str(call).lower() or "invalid" in str(call).lower() 
                      for call in error_calls)

    def test_file_not_found_logging(self, content_manager):
        """Test logging when content file is not found."""
        with patch.object(content_manager, "logger") as mock_logger:
            # Try to get non-existent content
            with pytest.raises(Exception):
                content = content_manager.get_content("notes", "non-existent")
            
            # Should log file not found
            mock_logger.warning.assert_called()
            warning_calls = mock_logger.warning.call_args_list
            assert any("not found" in str(call).lower() for call in warning_calls)

    def test_github_api_request_logging(self, content_manager):
        """Test logging of GitHub API requests."""
        with patch("app.main.httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"stargazers_count": 42}
            mock_response.headers = {"X-RateLimit-Remaining": "59"}
            mock_get.return_value = mock_response
            
            with patch.object(content_manager, "logger") as mock_logger:
                # Trigger GitHub API call
                stars = content_manager.get_github_stars("owner", "repo")
                
                # Should log API request
                mock_logger.info.assert_called()
                info_calls = mock_logger.info.call_args_list
                assert any("github" in str(call).lower() and "api" in str(call).lower() 
                          for call in info_calls)
                
                # Should log rate limit
                assert any("rate" in str(call).lower() and "limit" in str(call).lower() 
                          for call in info_calls)

    def test_github_api_error_logging(self, content_manager):
        """Test logging of GitHub API errors."""
        with patch("app.main.httpx.get") as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            with patch.object(content_manager, "logger") as mock_logger:
                # Trigger GitHub API error
                stars = content_manager.get_github_stars("owner", "repo")
                
                # Should log API error
                mock_logger.error.assert_called()
                error_calls = mock_logger.error.call_args_list
                assert any("github" in str(call).lower() and "error" in str(call).lower() 
                          for call in error_calls)

    def test_content_validation_logging(self, content_manager):
        """Test logging of content validation."""
        with patch.object(content_manager, "logger") as mock_logger:
            # Create content with validation issues
            content_data = {
                "title": "",  # Empty title
                "created": "invalid-date",  # Invalid date
                "tags": "not-a-list"  # Invalid tags
            }
            
            # Try to validate
            with pytest.raises(Exception):
                content_manager.validate_content(content_data)
            
            # Should log validation errors
            mock_logger.warning.assert_called()
            warning_calls = mock_logger.warning.call_args_list
            assert any("validation" in str(call).lower() for call in warning_calls)

    def test_performance_logging(self, content_manager):
        """Test logging of performance metrics."""
        with patch.object(content_manager, "logger") as mock_logger:
            with patch("time.time") as mock_time:
                # Simulate operation timing
                mock_time.side_effect = [0, 0.5]  # 500ms operation
                
                # Perform operation
                content = content_manager.get_all_content()
                
                # Should log performance metrics
                mock_logger.info.assert_called()
                info_calls = mock_logger.info.call_args_list
                assert any(("duration" in str(call).lower() or "time" in str(call).lower())
                          and "ms" in str(call).lower() for call in info_calls)

    def test_structured_logging_fields(self, content_manager):
        """Test that logs include structured fields."""
        with patch.object(content_manager, "logger") as mock_logger:
            # Perform operation
            content = content_manager.get_all_content()
            
            # Check that logs include structured data
            for call in mock_logger.info.call_args_list:
                if len(call[0]) > 0:  # Has positional args
                    continue
                    
                kwargs = call[1]  # Keyword arguments
                
                # Should include component name
                assert kwargs.get("component") == "ContentManager" or \
                       "ContentManager" in str(kwargs)
                
                # Should include operation context
                assert any(key in kwargs for key in 
                          ["operation", "action", "method", "function"])

    def test_cache_metrics_logging(self, content_manager):
        """Test logging of cache metrics."""
        with patch.object(content_manager, "logger") as mock_logger:
            # Perform multiple operations to generate cache metrics
            for _ in range(5):
                content_manager.get_all_content()
            
            # Clear cache
            content_manager._cache_clear()
            
            # Should log cache statistics
            mock_logger.info.assert_called()
            info_calls = mock_logger.info.call_args_list
            assert any("cache" in str(call).lower() and 
                      ("cleared" in str(call).lower() or "statistics" in str(call).lower())
                      for call in info_calls)

    def test_content_processing_pipeline_logging(self, content_manager):
        """Test logging throughout content processing pipeline."""
        with patch.object(content_manager, "logger") as mock_logger:
            # Process content through pipeline
            test_content = """---
title: Pipeline Test
created: 2024-01-01
---

Test content for pipeline.
"""
            
            processed = content_manager.parse_markdown_with_frontmatter(
                test_content,
                "notes",
                "pipeline-test"
            )
            
            # Should log each pipeline stage
            all_calls = (mock_logger.debug.call_args_list + 
                        mock_logger.info.call_args_list)
            
            # Check for pipeline stage logs
            pipeline_stages = ["parsing", "validation", "processing", "complete"]
            for stage in pipeline_stages:
                assert any(stage in str(call).lower() for call in all_calls), \
                       f"Missing log for pipeline stage: {stage}"