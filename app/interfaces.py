"""
Abstract interfaces for content management and backlink services.
These interfaces define contracts for dependency injection and testability.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass


@dataclass
class PathValidationResult:
    """Result of path validation operation."""
    success: bool
    errors: List[str]
    valid_slugs: List[str]
    invalid_slugs: List[str]


@dataclass  
class CircularReferenceResult:
    """Result of circular reference detection."""
    has_cycle: bool
    cycle_position: Optional[int] = None
    cycle_slug: Optional[str] = None


class IContentProvider(ABC):
    """Abstract interface for content management operations."""

    @abstractmethod
    def get_content_by_slug(
        self, content_type: str, slug: str
    ) -> Optional[Dict[str, Any]]:
        """Get content by type and slug.

        Args:
            content_type: The type of content (e.g., 'notes', 'til', 'bookmarks')
            slug: The unique slug identifier for the content

        Returns:
            Content data dictionary or None if not found
        """
        pass

    @abstractmethod
    def get_all_content(self) -> List[Dict[str, Any]]:
        """Get all content across all types.

        Returns:
            List of all content items
        """
        pass

    @abstractmethod
    def get_content_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get content filtered by tag.

        Args:
            tag: The tag to filter by

        Returns:
            List of content items with the specified tag
        """
        pass

    @abstractmethod
    def get_content(
        self, content_type: str, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get content by type with optional limit.

        Args:
            content_type: The type of content to retrieve
            limit: Optional maximum number of items to return

        Returns:
            Dictionary with 'content' list and metadata
        """
        pass

    @abstractmethod
    def get_bookmarks(self, limit: Optional[int] = 10) -> List[Dict[str, Any]]:
        """Get bookmark content with GitHub stars integration.

        Args:
            limit: Maximum number of bookmarks to return

        Returns:
            List of bookmark items with star counts
        """
        pass

    @abstractmethod
    def get_posts_by_tag(
        self, tag: str, content_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get content filtered by tag across content types.

        Args:
            tag: The tag to filter by
            content_types: Optional list of content types to include

        Returns:
            Dictionary with filtered posts and metadata
        """
        pass

    @abstractmethod
    async def get_mixed_content(
        self, page: int = 1, per_page: int = 10
    ) -> Dict[str, Any]:
        """Get paginated mixed content sorted by date.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Dictionary with paginated content and navigation info
        """
        pass

    @abstractmethod
    def get_tag_counts(self) -> Dict[str, int]:
        """Get count of content items per tag.

        Returns:
            Dictionary mapping tags to content counts
        """
        pass

    @abstractmethod
    def get_til_posts(self, page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """Get paginated TIL posts.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Dictionary with TIL posts and pagination info
        """
        pass

    @abstractmethod
    def get_til_posts_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get TIL posts filtered by tag.

        Args:
            tag: The tag to filter by

        Returns:
            List of TIL posts with the specified tag
        """
        pass

    @abstractmethod
    def render_markdown(self, file_path: str) -> Dict[str, Any]:
        """Render markdown file with frontmatter parsing.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary with rendered content and metadata
        """
        pass

    @abstractmethod
    async def get_homepage_sections(self) -> Dict[str, Any]:
        """Get content sections for homepage display.

        Returns:
            Dictionary with organized content sections
        """
        pass

    @abstractmethod
    def get_all_garden_content(self) -> Dict[str, Any]:
        """Get all content for garden visualization.

        Returns:
            Dictionary with all content organized for visualization
        """
        pass


class IBacklinkService(ABC):
    """Abstract interface for backlink analysis and management."""

    @abstractmethod
    def extract_internal_links(self, content: str, content_path: str) -> Set[str]:
        """Extract internal links from markdown content.

        Args:
            content: Raw markdown content
            content_path: Path to the content file for relative link resolution

        Returns:
            Set of normalized internal link targets (slugs or paths)
        """
        pass

    @abstractmethod
    def get_backlinks(self, target_slug: str) -> List[Dict[str, str]]:
        """Get all content that links to the target content.

        Args:
            target_slug: Slug of the target content

        Returns:
            List of dicts with 'source_slug', 'source_title', 'link_context'
        """
        pass

    @abstractmethod
    def get_forward_links(self, source_slug: str) -> List[Dict[str, str]]:
        """Get all links from the source content.

        Args:
            source_slug: Slug of the source content

        Returns:
            List of dicts with 'target_slug', 'target_title', 'link_text'
        """
        pass

    @abstractmethod
    def build_link_graph(self) -> Dict[str, List[str]]:
        """Build complete link graph for all content.

        Returns:
            Dict mapping source slugs to lists of target slugs
        """
        pass

    @abstractmethod
    def validate_links(self) -> List[Dict[str, str]]:
        """Validate all internal links and report broken ones.

        Returns:
            List of dicts with 'source_slug', 'broken_link', 'error'
        """
        pass

    @abstractmethod
    def get_orphaned_content(self) -> List[str]:
        """Find content with no incoming or outgoing links.

        Returns:
            List of content slugs that are orphaned
        """
        pass

    @abstractmethod
    def refresh_cache(self) -> None:
        """Refresh the backlink cache after content changes."""
        pass


class IPathNavigationService(ABC):
    """Abstract interface for path navigation and validation."""

    @abstractmethod
    def validate_exploration_path(self, path_string: str) -> PathValidationResult:
        """Validate exploration path with comprehensive checks.

        Args:
            path_string: Comma-separated string of note slugs (e.g., "note1,note2,note3")

        Returns:
            PathValidationResult with validation details
        """
        pass

    @abstractmethod
    def check_circular_references(self, path_notes: List[str]) -> CircularReferenceResult:
        """Check if path contains circular references.

        Args:
            path_notes: List of note slugs to check for cycles

        Returns:
            CircularReferenceResult with cycle detection details
        """
        pass
