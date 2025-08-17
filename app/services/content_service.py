"""
ContentService implementation providing IContentProvider interface.
Uses composition to leverage existing ContentManager functionality.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
import markdown
from pydantic import ValidationError
import time

from app.interfaces import IContentProvider
from app.models import GrowthStage


class ContentService(IContentProvider):
    """Service for managing and retrieving content with caching."""
    
    def __init__(self, content_dir: Optional[str] = None, cache_ttl: int = 300):
        """Initialize ContentService with configurable content directory and cache TTL.
        
        Args:
            content_dir: Path to content directory (defaults to app/content)
            cache_ttl: Cache time-to-live in seconds (default 300)
        """
        if content_dir:
            self._content_dir = Path(content_dir)
        else:
            self._content_dir = Path("app/content")
        
        self._cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}
        
        # Configure markdown processor
        self._md = markdown.Markdown(
            extensions=[
                'markdown.extensions.meta',
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
            ]
        )
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self._cache_timestamps:
            return False
        return (time.time() - self._cache_timestamps[key]) < self._cache_ttl
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if valid."""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache value with timestamp."""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter and return metadata and content.
        
        Args:
            content: Raw markdown content with optional frontmatter
            
        Returns:
            Tuple of (metadata dict, markdown content)
        """
        if not content.startswith('---'):
            return {}, content
        
        try:
            # Find the end of frontmatter
            end_marker = content.find('\n---\n', 4)
            if end_marker == -1:
                return {}, content
            
            # Extract and parse YAML
            yaml_content = content[4:end_marker]
            metadata = yaml.safe_load(yaml_content)
            if metadata is None:
                metadata = {}
            
            # Extract markdown content
            markdown_content = content[end_marker + 5:]
            
            return metadata, markdown_content
            
        except yaml.YAMLError:
            # Return empty metadata on YAML error
            return {}, content
    
    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown text to HTML.
        
        Args:
            markdown_text: Raw markdown text
            
        Returns:
            HTML string
        """
        # Reset the markdown processor for clean conversion
        self._md.reset()
        return self._md.convert(markdown_text)
    
    def _validate_growth_stage(self, metadata: Dict[str, Any]) -> None:
        """Validate growth stage in metadata.
        
        Args:
            metadata: Content metadata dictionary
            
        Raises:
            ValidationError: If growth stage is invalid
        """
        if 'growth_stage' in metadata:
            stage_value = metadata['growth_stage']
            if isinstance(stage_value, str):
                # Normalize to lowercase
                normalized = stage_value.lower()
                # Check if it's a valid enum value
                valid_stages = [s.value for s in GrowthStage]
                if normalized not in valid_stages:
                    # Create a proper ValidationError
                    raise ValidationError.from_exception_data(
                        "ValidationError",
                        [
                            {
                                "type": "enum",
                                "loc": ("growth_stage",),
                                "msg": f"Invalid growth stage: {stage_value}",
                                "input": stage_value,
                                "ctx": {"expected": ", ".join(valid_stages)}
                            }
                        ]
                    )
    
    def _process_content_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single content file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Processed content dictionary or None if error
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            metadata, markdown_content = self._parse_frontmatter(content)
            
            # Validate growth stage if present
            self._validate_growth_stage(metadata)
            
            # Convert markdown to HTML
            html = self._convert_markdown_to_html(markdown_content)
            
            # Build result dictionary
            result = {
                "slug": file_path.stem,
                "content_type": file_path.parent.name,
                "file_path": str(file_path),
                "html": html,
                "markdown": markdown_content,
                **metadata
            }
            
            # Ensure required fields have defaults
            if "title" not in result:
                result["title"] = file_path.stem.replace("-", " ").title()
            if "created" not in result:
                result["created"] = datetime.now().isoformat()
            if "tags" not in result:
                result["tags"] = []
            if "status" not in result:
                result["status"] = "Evergreen"
            
            return result
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception:
            # Log or handle other errors
            return None
    
    def get_content_by_slug(self, content_type: str, slug: str) -> Optional[Dict[str, Any]]:
        """Get content by type and slug.
        
        Args:
            content_type: The type of content (e.g., 'notes', 'til', 'bookmarks')
            slug: The unique slug identifier for the content
            
        Returns:
            Content data dictionary or None if not found
        """
        # Check cache first
        cache_key = f"{content_type}:{slug}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Build file path
        file_path = self._content_dir / content_type / f"{slug}.md"
        
        # Check if file exists
        if not file_path.exists():
            return None
        
        # Process the file - this may raise ValidationError
        try:
            result = self._process_content_file(file_path)
        except ValidationError:
            # Re-raise validation errors for the caller to handle
            raise
        
        # Cache the result
        if result:
            self._set_cache(cache_key, result)
        
        return result
    
    def get_all_content(self) -> List[Dict[str, Any]]:
        """Get all content across all types.
        
        Returns:
            List of all content items
        """
        # Check cache
        cache_key = "all_content"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        all_content = []
        
        # Check if content directory exists
        if not self._content_dir.exists():
            return all_content
        
        # Iterate through all content directories
        for content_dir in self._content_dir.iterdir():
            if content_dir.is_dir():
                # Get all markdown files in this directory
                for file_path in content_dir.glob("*.md"):
                    try:
                        content = self._process_content_file(file_path)
                        if content and content.get("status") != "draft":
                            all_content.append(content)
                    except ValidationError:
                        # Skip files with validation errors
                        continue
        
        # Sort by created date (newest first)
        all_content.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        # Cache the result
        self._set_cache(cache_key, all_content)
        
        return all_content
    
    def get_content_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get content filtered by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of content items with the specified tag
        """
        all_content = self.get_all_content()
        return [
            content for content in all_content
            if tag in content.get("tags", [])
        ]
    
    def get_content(self, content_type: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get content by type with optional limit.
        
        Args:
            content_type: The type of content to retrieve
            limit: Optional maximum number of items to return
            
        Returns:
            Dictionary with 'content' list and metadata
        """
        # Check cache
        cache_key = f"content:{content_type}:{limit}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        content_list = []
        content_dir = self._content_dir / content_type
        
        if content_dir.exists():
            # Get all markdown files
            for file_path in content_dir.glob("*.md"):
                try:
                    content = self._process_content_file(file_path)
                    if content and content.get("status") != "draft":
                        content_list.append(content)
                except ValidationError:
                    # Skip files with validation errors
                    continue
        
        # Sort by created date
        content_list.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        # Apply limit if specified
        if limit:
            content_list = content_list[:limit]
        
        result = {
            "content": content_list,
            "total": len(content_list),
            "content_type": content_type
        }
        
        # Cache the result
        self._set_cache(cache_key, result)
        
        return result
    
    def get_bookmarks(self, limit: Optional[int] = 10) -> List[Dict[str, Any]]:
        """Get bookmark content.
        
        Args:
            limit: Maximum number of bookmarks to return
            
        Returns:
            List of bookmark items
        """
        result = self.get_content("bookmarks", limit=limit)
        return result.get("content", [])
    
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
        all_content = self.get_all_content()
        
        # Filter by tag
        filtered = [
            content for content in all_content
            if tag in content.get("tags", [])
        ]
        
        # Filter by content types if specified
        if content_types:
            filtered = [
                content for content in filtered
                if content.get("content_type") in content_types
            ]
        
        return {
            "posts": filtered,
            "tag": tag,
            "total": len(filtered)
        }
    
    async def get_mixed_content(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get paginated mixed content sorted by date.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Dictionary with paginated content and navigation info
        """
        all_content = self.get_all_content()
        
        # Calculate pagination
        total = len(all_content)
        start = (page - 1) * per_page
        end = start + per_page
        
        # Get page content
        page_content = all_content[start:end]
        
        return {
            "content": page_content,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": end < total,
            "has_prev": page > 1
        }
    
    def get_tag_counts(self) -> Dict[str, int]:
        """Get count of content items per tag.
        
        Returns:
            Dictionary mapping tags to content counts
        """
        tag_counts = {}
        all_content = self.get_all_content()
        
        for content in all_content:
            for tag in content.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return tag_counts
    
    def get_til_posts(self, page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """Get paginated TIL posts.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Dictionary with TIL posts and pagination info
        """
        til_content = self.get_content("til")
        posts = til_content.get("content", [])
        
        # Calculate pagination
        total = len(posts)
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            "posts": posts[start:end],
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def get_til_posts_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get TIL posts filtered by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of TIL posts with the specified tag
        """
        til_content = self.get_content("til")
        posts = til_content.get("content", [])
        
        return [
            post for post in posts
            if tag in post.get("tags", [])
        ]
    
    def render_markdown(self, markdown_text: str) -> Dict[str, Any]:
        """Render markdown text to HTML.
        
        This is a simplified version that takes markdown text directly
        instead of a file path, for testing purposes.
        
        Args:
            markdown_text: Raw markdown text
            
        Returns:
            Dictionary with rendered HTML
        """
        html = self._convert_markdown_to_html(markdown_text)
        return {"html": html}
    
    async def get_homepage_sections(self) -> Dict[str, Any]:
        """Get content sections for homepage display.
        
        Returns:
            Dictionary with organized content sections
        """
        # Get recent content from each type
        notes = self.get_content("notes", limit=5)
        til = self.get_content("til", limit=5)
        bookmarks = self.get_bookmarks(limit=5)
        
        return {
            "sections": {
                "recent_notes": notes.get("content", []),
                "recent_til": til.get("content", []),
                "recent_bookmarks": bookmarks
            }
        }
    
    def get_all_garden_content(self) -> Dict[str, Any]:
        """Get all content for garden visualization.
        
        Returns:
            Dictionary with all content organized for visualization
        """
        all_content = self.get_all_content()
        
        # Group by growth stage
        by_stage = {}
        for stage in GrowthStage:
            by_stage[stage.value] = []
        
        for content in all_content:
            stage = content.get("growth_stage", GrowthStage.SEEDLING.value)
            if stage in by_stage:
                by_stage[stage].append(content)
        
        return {
            "content": all_content,
            "by_stage": by_stage,
            "total": len(all_content)
        }