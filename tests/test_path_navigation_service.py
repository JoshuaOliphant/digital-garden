"""
Test suite for PathNavigationService implementation following strict TDD principles.
All tests should fail initially and pass after implementation.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, Optional

# Test fixtures and mock data
@pytest.fixture
def mock_content_service():
    """Mock ContentService for testing PathNavigationService integration."""
    mock = Mock()
    # Mock existing content
    mock.get_content_by_slug.side_effect = lambda content_type, slug: {
        'note1': {'title': 'Note 1', 'slug': 'note1'},
        'note2': {'title': 'Note 2', 'slug': 'note2'}, 
        'note3': {'title': 'Note 3', 'slug': 'note3'},
        'circular1': {'title': 'Circular 1', 'slug': 'circular1'},
        'circular2': {'title': 'Circular 2', 'slug': 'circular2'},
        'valid-note': {'title': 'Valid Note', 'slug': 'valid-note'},
        'another-note': {'title': 'Another Note', 'slug': 'another-note'},
    }.get(slug, None)
    return mock

@pytest.fixture
def sample_valid_path():
    """Sample valid path string for testing."""
    return "note1,note2,note3"

@pytest.fixture  
def sample_invalid_path():
    """Sample path with non-existent slugs."""
    return "note1,missing-note,note3"

@pytest.fixture
def sample_circular_path():
    """Sample path with circular references."""
    return "note1,note2,note1"

@pytest.fixture
def sample_long_path():
    """Sample path exceeding maximum length."""
    return "note1,note2,note3,note1,note2,note3,note1,note2,note3,note1,note2"


class TestPathNavigationServiceInterface:
    """Test PathNavigationService interface implementation."""
    
    def test_service_implements_interface(self):
        """Test 1: Verify PathNavigationService implements IPathNavigationService."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            from app.interfaces import IPathNavigationService
            
            assert issubclass(PathNavigationService, IPathNavigationService), \
                "PathNavigationService should implement IPathNavigationService interface"
                
        except ImportError as e:
            pytest.fail(f"PathNavigationService should exist and be importable: {e}")
    
    def test_service_can_be_instantiated_with_content_service(self, mock_content_service):
        """Test 2: Verify service accepts ContentService dependency."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            assert service is not None, "Should instantiate with content service"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_service_has_required_methods(self, mock_content_service):
        """Test 3: Verify service has all interface methods."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            
            assert hasattr(service, 'validate_exploration_path'), \
                "Should have validate_exploration_path method"
            assert hasattr(service, 'check_circular_references'), \
                "Should have check_circular_references method"
            assert callable(service.validate_exploration_path), \
                "validate_exploration_path should be callable"
            assert callable(service.check_circular_references), \
                "check_circular_references should be callable"
                
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


class TestPathValidation:
    """Test path validation functionality."""
    
    def test_validate_valid_path_returns_success(self, mock_content_service, sample_valid_path):
        """Test 4: Valid path should return success result."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path(sample_valid_path)
            
            assert result.success is True, "Valid path should be successful"
            assert len(result.errors) == 0, "Valid path should have no errors"
            assert result.valid_slugs == ['note1', 'note2', 'note3'], \
                "Should return all valid slugs"
            assert len(result.invalid_slugs) == 0, "Valid path should have no invalid slugs"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_validate_invalid_slugs_returns_failure(self, mock_content_service, sample_invalid_path):
        """Test 5: Path with invalid slugs should return failure."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path(sample_invalid_path)
            
            assert result.success is False, "Invalid path should fail validation"
            assert len(result.errors) > 0, "Should have error messages"
            assert 'missing-note' in result.invalid_slugs, \
                "Should identify invalid slug"
            assert 'note1' in result.valid_slugs, "Should identify valid slugs"
            assert 'note3' in result.valid_slugs, "Should identify valid slugs"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_validate_empty_path_returns_failure(self, mock_content_service):
        """Test 6: Empty path should return failure."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path("")
            
            assert result.success is False, "Empty path should fail validation"
            assert len(result.errors) > 0, "Should have error message"
            assert "empty" in result.errors[0].lower() or "invalid" in result.errors[0].lower(), \
                "Should mention empty or invalid path"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_validate_whitespace_only_path_returns_failure(self, mock_content_service):
        """Test 7: Whitespace-only path should return failure."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path("   \t\n   ")
            
            assert result.success is False, "Whitespace path should fail validation"
            assert len(result.errors) > 0, "Should have error message"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_validate_single_note_path_succeeds(self, mock_content_service):
        """Test 8: Single valid note should succeed."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path("note1")
            
            assert result.success is True, "Single valid note should succeed"
            assert result.valid_slugs == ['note1'], "Should return single valid slug"
            assert len(result.invalid_slugs) == 0, "Should have no invalid slugs"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


class TestPathLengthValidation:
    """Test path length constraints."""
    
    def test_validate_maximum_length_path_succeeds(self, mock_content_service):
        """Test 9: Path with exactly 10 notes should succeed."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            # Create path with exactly 10 valid notes
            max_path = ",".join([f"note{i%3+1}" for i in range(10)])
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path(max_path)
            
            assert result.success is True, "Path with 10 notes should succeed"
            assert len(result.valid_slugs) == 10, "Should have 10 valid slugs"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_validate_over_maximum_length_fails(self, mock_content_service, sample_long_path):
        """Test 10: Path exceeding 10 notes should fail."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path(sample_long_path)
            
            assert result.success is False, "Path over 10 notes should fail"
            assert len(result.errors) > 0, "Should have error message"
            assert any("10" in error or "maximum" in error.lower() or "too long" in error.lower() 
                     for error in result.errors), \
                "Should mention length limit in error"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


class TestCircularReferenceDetection:
    """Test circular reference detection."""
    
    def test_check_no_circular_references(self, mock_content_service):
        """Test 11: Path without cycles should return no circular references."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.check_circular_references(['note1', 'note2', 'note3'])
            
            assert result.has_cycle is False, "Should detect no circular references"
            assert result.cycle_position is None, "Should have no cycle position"
            assert result.cycle_slug is None, "Should have no cycle slug"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_check_direct_circular_reference(self, mock_content_service):
        """Test 12: Direct circular reference should be detected."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.check_circular_references(['note1', 'note2', 'note1'])
            
            assert result.has_cycle is True, "Should detect circular reference"
            assert result.cycle_position == 2, "Should identify cycle position"
            assert result.cycle_slug == 'note1', "Should identify cycle slug"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_check_complex_circular_reference(self, mock_content_service):
        """Test 13: Complex circular pattern should be detected."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.check_circular_references(['note1', 'note2', 'note3', 'note2'])
            
            assert result.has_cycle is True, "Should detect circular reference"
            assert result.cycle_position == 3, "Should identify cycle position"
            assert result.cycle_slug == 'note2', "Should identify cycle slug"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_validate_path_detects_circular_references(self, mock_content_service, sample_circular_path):
        """Test 14: Path validation should detect circular references."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path(sample_circular_path)
            
            assert result.success is False, "Circular path should fail validation"
            assert any("circular" in error.lower() or "cycle" in error.lower() 
                     for error in result.errors), \
                "Should mention circular reference in errors"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


class TestPathParsing:
    """Test path string parsing functionality."""
    
    def test_parse_comma_separated_path(self, mock_content_service):
        """Test 15: Comma-separated path should be parsed correctly."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path("note1,note2,note3")
            
            assert len(result.valid_slugs) == 3, "Should parse 3 slugs"
            assert result.valid_slugs == ['note1', 'note2', 'note3'], \
                "Should maintain order"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_parse_path_with_spaces(self, mock_content_service):
        """Test 16: Path with spaces around commas should be handled."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path("note1 , note2  ,  note3")
            
            assert result.valid_slugs == ['note1', 'note2', 'note3'], \
                "Should trim whitespace and parse correctly"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_parse_path_with_empty_segments(self, mock_content_service):
        """Test 17: Path with empty segments should be handled gracefully."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path("note1,,note2,")
            
            assert result.success is False, "Empty segments should cause failure"
            assert len(result.errors) > 0, "Should have error for empty segments"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


class TestContentServiceIntegration:
    """Test integration with ContentService."""
    
    def test_uses_content_service_for_validation(self, mock_content_service):
        """Test 18: Should use ContentService to validate slug existence."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            service.validate_exploration_path("note1,note2")
            
            # Verify ContentService was called
            assert mock_content_service.get_content_by_slug.called, \
                "Should call ContentService to validate slugs"
            
            # Check specific calls
            calls = mock_content_service.get_content_by_slug.call_args_list
            assert len(calls) >= 2, "Should call for each slug"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_handles_content_service_errors(self, mock_content_service):
        """Test 19: Should handle ContentService exceptions gracefully."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            # Mock ContentService to raise exception
            mock_content_service.get_content_by_slug.side_effect = Exception("Content service error")
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path("note1")
            
            assert result.success is False, "Should fail when ContentService errors"
            assert len(result.errors) > 0, "Should have error message"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


class TestErrorHandling:
    """Test comprehensive error handling."""
    
    def test_handles_none_input(self, mock_content_service):
        """Test 20: Should handle None input gracefully."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path(None)
            
            assert result.success is False, "None input should fail"
            assert len(result.errors) > 0, "Should have error message"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_handles_non_string_input(self, mock_content_service):
        """Test 21: Should handle non-string input gracefully."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.validate_exploration_path(123)
            
            assert result.success is False, "Non-string input should fail"
            assert len(result.errors) > 0, "Should have error message"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_check_circular_references_handles_none_input(self, mock_content_service):
        """Test 22: Circular check should handle None input."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.check_circular_references(None)
            
            assert result.has_cycle is False, "None input should return no cycle"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")
    
    def test_check_circular_references_handles_empty_list(self, mock_content_service):
        """Test 23: Circular check should handle empty list."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            
            service = PathNavigationService(mock_content_service)
            result = service.check_circular_references([])
            
            assert result.has_cycle is False, "Empty list should return no cycle"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""
    
    def test_performance_with_large_valid_path(self, mock_content_service):
        """Test 24: Should handle large valid paths efficiently."""
        try:
            from app.services.path_navigation_service import PathNavigationService
            import time
            
            # Create path with 10 valid notes (maximum allowed)
            large_path = ",".join([f"note{i%3+1}" for i in range(10)])
            
            service = PathNavigationService(mock_content_service)
            
            start_time = time.time()
            result = service.validate_exploration_path(large_path)
            end_time = time.time()
            
            # Should complete within reasonable time (less than 1 second)
            assert (end_time - start_time) < 1.0, "Should complete within 1 second"
            assert result.success is True, "Large valid path should succeed"
            
        except ImportError:
            pytest.fail("PathNavigationService should be importable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])