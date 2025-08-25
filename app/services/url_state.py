"""
URLStateParser service for parsing and validating URL query parameters.

This service handles URL parameter parsing for filtering, sorting, and pagination
with proper validation and default handling.
"""

from typing import Dict, List, Optional, Any
from urllib.parse import unquote
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SortField(str, Enum):
    """Valid sort fields for content."""

    CREATED = "created"
    UPDATED = "updated"
    TITLE = "title"


class SortOrder(str, Enum):
    """Valid sort order directions."""

    ASC = "asc"
    DESC = "desc"


class URLState(BaseModel):
    """Structured representation of URL query parameters."""

    types: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    growth: List[str] = Field(default_factory=list)
    sort: str = Field(default=SortField.CREATED.value)
    order: str = Field(default=SortOrder.DESC.value)
    page: int = Field(default=1)

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: Any) -> str:
        """Validate sort field is allowed."""
        if v is None or str(v) not in [field.value for field in SortField]:
            return SortField.CREATED.value
        return str(v)

    @field_validator("order")
    @classmethod
    def validate_order(cls, v: Any) -> str:
        """Validate order direction is allowed."""
        if v is None or str(v) not in [order.value for order in SortOrder]:
            return SortOrder.DESC.value
        return str(v)

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: Any) -> int:
        """Validate page is a positive integer."""
        try:
            page = int(v)
            return max(1, page)
        except (TypeError, ValueError):
            return 1


class URLStateParser:
    """Service for parsing URL query parameters into structured state."""

    def parse(self, params: Dict[str, Any]) -> URLState:
        """Parse query parameters into URLState.

        Args:
            params: Dictionary of query parameters

        Returns:
            URLState with parsed and validated parameters
        """
        parsed = {
            "types": self._parse_list(params.get("types")),
            "tags": self._parse_list(params.get("tags")),
            "growth": self._parse_list(params.get("growth")),
            "sort": self._parse_value(params.get("sort")),
            "order": self._parse_value(params.get("order")),
            "page": self._parse_page(params.get("page")),
        }

        # Remove None values to use defaults
        parsed = {k: v for k, v in parsed.items() if v is not None}

        return URLState(**parsed)

    def _parse_list(self, value: Optional[Any]) -> List[str]:
        """Parse comma-separated string into list.

        Args:
            value: String value or None

        Returns:
            List of parsed values
        """
        if value is None:
            return []

        # Convert to string if needed
        value = str(value)

        # Handle empty string
        if not value or value.strip() == "":
            return []

        # URL decode the value
        value = unquote(value)

        # Split by comma and clean whitespace
        items = []
        for item in value.split(","):
            item = item.strip()
            if item:  # Skip empty items
                # URL decode individual items in case they were encoded separately
                items.append(unquote(item))

        return items

    def _parse_page(self, value: Optional[Any]) -> Optional[int]:
        """Parse and validate page number.

        Args:
            value: Page value or None

        Returns:
            Valid page number or None to use default
        """
        if value is None:
            return None

        try:
            page = int(value)
            # Return None for invalid pages to use default
            if page < 1:
                return None
            return page
        except (TypeError, ValueError):
            return None

    def _parse_value(self, value: Optional[Any]) -> Optional[str]:
        """Parse value to string or None.

        Args:
            value: Value of any type

        Returns:
            String value or None to use default
        """
        if value is None:
            return None
        return str(value)
