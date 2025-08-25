"""
Tests for URLStateParser service.

This test suite verifies URL parameter parsing functionality including
comma-separated values, validation, and default handling.
"""

from app.services.url_state import URLStateParser


class TestURLStateParser:
    """Test the URLStateParser service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = URLStateParser()

    def test_parse_empty_params_returns_defaults(self):
        """Test that empty params return sensible defaults."""
        result = self.parser.parse({})

        assert result.types == []
        assert result.tags == []
        assert result.growth == []
        assert result.sort == "created"
        assert result.order == "desc"
        assert result.page == 1

    def test_parse_types_comma_separated(self):
        """Test that comma-separated types are parsed to list."""
        params = {"types": "notes,til"}
        result = self.parser.parse(params)

        assert result.types == ["notes", "til"]

    def test_parse_tags_comma_separated(self):
        """Test that comma-separated tags are parsed to list."""
        params = {"tags": "python,htmx"}
        result = self.parser.parse(params)

        assert result.tags == ["python", "htmx"]

    def test_parse_growth_stages_comma_separated(self):
        """Test that comma-separated growth stages are parsed."""
        params = {"growth": "seedling,evergreen"}
        result = self.parser.parse(params)

        assert result.growth == ["seedling", "evergreen"]

    def test_parse_sort_field_with_validation(self):
        """Test that only valid sort fields are accepted."""
        # Valid sort fields
        valid_fields = ["created", "updated", "title"]
        for field in valid_fields:
            params = {"sort": field}
            result = self.parser.parse(params)
            assert result.sort == field

        # Invalid sort field should default to "created"
        params = {"sort": "invalid_field"}
        result = self.parser.parse(params)
        assert result.sort == "created"

    def test_parse_order_direction_validation(self):
        """Test that only 'asc' or 'desc' are allowed for order."""
        # Valid orders
        params = {"order": "asc"}
        result = self.parser.parse(params)
        assert result.order == "asc"

        params = {"order": "desc"}
        result = self.parser.parse(params)
        assert result.order == "desc"

        # Invalid order should default to "desc"
        params = {"order": "invalid"}
        result = self.parser.parse(params)
        assert result.order == "desc"

    def test_parse_page_number_validation(self):
        """Test that page must be a positive integer."""
        # Valid page numbers
        params = {"page": "1"}
        result = self.parser.parse(params)
        assert result.page == 1

        params = {"page": "42"}
        result = self.parser.parse(params)
        assert result.page == 42

        # Invalid page numbers should default to 1
        invalid_pages = ["0", "-1", "abc", "1.5", ""]
        for invalid_page in invalid_pages:
            params = {"page": invalid_page}
            result = self.parser.parse(params)
            assert result.page == 1

    def test_parse_invalid_params_returns_defaults(self):
        """Test that malformed params are handled gracefully."""
        # Various malformed inputs
        malformed_params = [
            {"types": ""},  # Empty string
            {"tags": ",,,"},  # Only commas
            {"growth": "seedling,,evergreen"},  # Double commas
            {"sort": None},  # None value
            {"order": 123},  # Wrong type
            {"page": None},  # None page
        ]

        for params in malformed_params:
            result = self.parser.parse(params)
            # Should not raise errors and return valid defaults
            assert isinstance(result.types, list)
            assert isinstance(result.tags, list)
            assert isinstance(result.growth, list)
            assert result.sort in ["created", "updated", "title"]
            assert result.order in ["asc", "desc"]
            assert result.page >= 1

    def test_parse_all_params_together(self):
        """Test parsing all parameters together."""
        params = {
            "types": "notes,til,bookmarks",
            "tags": "python,fastapi,htmx",
            "growth": "budding,growing,evergreen",
            "sort": "updated",
            "order": "asc",
            "page": "3",
        }
        result = self.parser.parse(params)

        assert result.types == ["notes", "til", "bookmarks"]
        assert result.tags == ["python", "fastapi", "htmx"]
        assert result.growth == ["budding", "growing", "evergreen"]
        assert result.sort == "updated"
        assert result.order == "asc"
        assert result.page == 3

    def test_parse_whitespace_handling(self):
        """Test that whitespace is handled in comma-separated values."""
        params = {
            "types": "notes, til , bookmarks",
            "tags": " python , fastapi , htmx ",
        }
        result = self.parser.parse(params)

        assert result.types == ["notes", "til", "bookmarks"]
        assert result.tags == ["python", "fastapi", "htmx"]

    def test_parse_url_encoded_values(self):
        """Test that URL-encoded values are handled properly."""
        params = {
            "tags": "c%2B%2B,c%23",  # URL encoded c++, c#
        }
        result = self.parser.parse(params)

        # Parser should handle URL decoding
        assert result.tags == ["c++", "c#"]
