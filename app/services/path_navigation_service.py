"""
PathNavigationService implementation for validating exploration paths and detecting circular references.

Implements the IPathNavigationService interface with comprehensive path validation,
slug existence checking, and circular reference detection capabilities.
"""

import logging
from typing import List, Optional, Tuple
from app.interfaces import (
    IPathNavigationService,
    IContentProvider,
    PathValidationResult,
    CircularReferenceResult,
)


logger = logging.getLogger(__name__)

# Constants
MAX_PATH_LENGTH = 10
CIRCULAR_DETECTION_RANGE = 2


class PathNavigationService(IPathNavigationService):
    """
    Service for validating exploration paths and detecting circular references.

    Features:
    - Comma-separated path parsing with validation
    - ContentService integration for slug existence checking
    - Path length enforcement (maximum 10 notes)
    - Circular reference detection
    - Comprehensive error handling and reporting
    """

    def __init__(self, content_service: IContentProvider):
        """
        Initialize PathNavigationService with content service dependency.

        Args:
            content_service: Service for accessing content data and validating slugs
        """
        self._content_service = content_service

    def _create_error_result(self, errors: List[str]) -> PathValidationResult:
        """Create standardized error result."""
        return PathValidationResult(
            success=False, errors=errors, valid_slugs=[], invalid_slugs=[]
        )

    def _validate_input_string(self, path_string) -> Optional[PathValidationResult]:
        """Validate input string and return error result if invalid, None if valid."""
        if path_string is None:
            return self._create_error_result(["Path string cannot be None"])
        if not isinstance(path_string, str):
            return self._create_error_result(["Path string must be a string"])
        if not path_string.strip():
            return self._create_error_result(["Path string cannot be empty"])
        return None

    def _parse_path_string(
        self, path_string: str
    ) -> Tuple[List[str], Optional[PathValidationResult]]:
        """Parse path string into slugs, return (slugs, error_result)."""
        raw_slugs = [slug.strip() for slug in path_string.split(",")]
        slugs = [slug for slug in raw_slugs if slug]

        if len(slugs) != len(raw_slugs):
            return [], self._create_error_result(["Path contains empty segments"])

        if len(slugs) > MAX_PATH_LENGTH:
            return [], self._create_error_result(
                [f"Path exceeds maximum length of {MAX_PATH_LENGTH} notes"]
            )

        return slugs, None

    def _check_short_range_cycles(self, slugs: List[str]) -> Optional[str]:
        """Check for short-range circular references. Returns error message if found."""
        for i, slug in enumerate(slugs):
            start_check = max(0, i - CIRCULAR_DETECTION_RANGE)
            if slug in slugs[start_check:i]:
                first_occurrence = start_check + slugs[start_check:i].index(slug)
                return f"Path contains circular reference: '{slug}' appears again at position {i} (first seen at position {first_occurrence})"
        return None

    def _validate_slugs_existence(
        self, slugs: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Validate slug existence against ContentService."""
        valid_slugs = []
        invalid_slugs = []

        for slug in slugs:
            content = self._content_service.get_content_by_slug("notes", slug)
            if content is not None:
                valid_slugs.append(slug)
            else:
                invalid_slugs.append(slug)

        return valid_slugs, invalid_slugs

    def validate_exploration_path(self, path_string: str) -> PathValidationResult:
        """Validate exploration path with comprehensive checks.

        Args:
            path_string: Comma-separated string of note slugs (e.g., "note1,note2,note3")

        Returns:
            PathValidationResult with validation details
        """
        # Input validation
        input_error = self._validate_input_string(path_string)
        if input_error:
            return input_error

        try:
            # Parse path string
            slugs, parse_error = self._parse_path_string(path_string)
            if parse_error:
                return parse_error

            # Check for short-range circular references
            cycle_error = self._check_short_range_cycles(slugs)
            if cycle_error:
                return self._create_error_result([cycle_error])

            # Validate slug existence using ContentService
            valid_slugs, invalid_slugs = self._validate_slugs_existence(slugs)

            # Build result
            success = len(invalid_slugs) == 0
            errors = []
            if invalid_slugs:
                errors.append(f"Invalid slugs found: {', '.join(invalid_slugs)}")

            return PathValidationResult(
                success=success,
                errors=errors,
                valid_slugs=valid_slugs,
                invalid_slugs=invalid_slugs,
            )

        except Exception as e:
            logger.error(f"Error validating exploration path: {e}")
            return self._create_error_result([f"Error validating path: {str(e)}"])

    def check_circular_references(
        self, path_notes: List[str]
    ) -> CircularReferenceResult:
        """Check if path contains circular references.

        Args:
            path_notes: List of note slugs to check for cycles

        Returns:
            CircularReferenceResult with cycle detection details
        """
        # Handle None input
        if path_notes is None:
            return CircularReferenceResult(has_cycle=False)

        # Handle empty list
        if not path_notes:
            return CircularReferenceResult(has_cycle=False)

        # Check for duplicates (circular references)
        seen_slugs = set()
        for i, slug in enumerate(path_notes):
            if slug in seen_slugs:
                return CircularReferenceResult(
                    has_cycle=True, cycle_position=i, cycle_slug=slug
                )
            seen_slugs.add(slug)

        # No circular references found
        return CircularReferenceResult(has_cycle=False)
