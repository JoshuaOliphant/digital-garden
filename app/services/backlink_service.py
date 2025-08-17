"""
BacklinkService implementation for discovering and managing content relationships.

Implements the IBacklinkService interface with comprehensive link discovery,
caching, and relationship mapping capabilities.
"""

import re
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from urllib.parse import urlparse

from app.interfaces import IBacklinkService, IContentProvider


logger = logging.getLogger(__name__)


class BacklinkService(IBacklinkService):
    """
    Service for discovering and managing content relationships through internal links.

    Features:
    - Multiple link format support (markdown, wiki-style, relative paths)
    - TTL-based caching with automatic refresh
    - Bidirectional link graph construction
    - Link validation and orphan detection
    """

    def __init__(self, content_provider: IContentProvider, cache_ttl_minutes: int = 5):
        """
        Initialize BacklinkService with content provider dependency.

        Args:
            content_provider: Service for accessing content data
            cache_ttl_minutes: Cache time-to-live in minutes
        """
        self._content_provider = content_provider
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._backlinks_cache: Dict[str, List[Dict[str, str]]] = {}
        self._link_graph_cache: Optional[Dict[str, List[str]]] = None
        self._cache_time: Optional[datetime] = None

        # Regex patterns for different link formats
        self._markdown_link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        self._wiki_link_pattern = re.compile(r"\[\[([^\]]+)\]\]")

    def extract_internal_links(self, content: str, content_path: str) -> Set[str]:
        """
        Extract internal links from markdown content.

        Args:
            content: Raw markdown content
            content_path: Path to the content file for relative link resolution

        Returns:
            Set of normalized internal link targets (slugs or paths)
        """
        if not content:
            return set()

        links = set()

        try:
            # Extract markdown-style links
            markdown_matches = self._markdown_link_pattern.findall(content)
            for link_text, link_target in markdown_matches:
                if self._is_internal_link(link_target):
                    normalized_target = self._normalize_link_target(
                        link_target, content_path
                    )
                    if normalized_target:
                        links.add(normalized_target)

            # Extract wiki-style links
            wiki_matches = self._wiki_link_pattern.findall(content)
            for link_target in wiki_matches:
                normalized_target = self._normalize_wiki_link(link_target.strip())
                if normalized_target:
                    links.add(normalized_target)

        except Exception as e:
            logger.error(f"Error extracting links from content at {content_path}: {e}")
            return set()

        return links

    def get_backlinks(self, target_slug: str) -> List[Dict[str, str]]:
        """
        Get all content that links to the target content.

        Args:
            target_slug: Slug of the target content

        Returns:
            List of dicts with 'source_slug', 'source_title', 'link_context'
        """
        if self._is_cache_valid() and target_slug in self._backlinks_cache:
            return self._backlinks_cache[target_slug]

        backlinks = []

        try:
            all_content = self._content_provider.get_all_content()

            for content_item in all_content:
                source_slug = content_item.get("slug", "")
                source_title = content_item.get("title", source_slug)
                content_text = content_item.get("content", "")
                content_path = content_item.get("file_path", "")

                # Skip self-references
                if source_slug == target_slug:
                    continue

                # Extract links from this content
                internal_links = self.extract_internal_links(content_text, content_path)

                # Check if any links point to our target
                for link in internal_links:
                    if self._link_matches_target(link, target_slug):
                        # Extract context around the link
                        link_context = self._extract_link_context(
                            content_text, link, target_slug
                        )

                        backlinks.append(
                            {
                                "source_slug": source_slug,
                                "source_title": source_title,
                                "link_context": link_context,
                            }
                        )
                        break

        except Exception as e:
            logger.error(f"Error getting backlinks for {target_slug}: {e}")
            return []

        # Update cache
        self._backlinks_cache[target_slug] = backlinks
        self._cache_time = datetime.now()

        return backlinks

    def get_forward_links(self, source_slug: str) -> List[Dict[str, str]]:
        """
        Get all links from the source content.

        Args:
            source_slug: Slug of the source content

        Returns:
            List of dicts with 'target_slug', 'target_title', 'link_text'
        """
        try:
            # Get the source content
            all_content = self._content_provider.get_all_content()
            source_content = None

            for content_item in all_content:
                if content_item.get("slug") == source_slug:
                    source_content = content_item
                    break

            if not source_content:
                return []

            content_text = source_content.get("content", "")
            content_path = source_content.get("file_path", "")

            # Extract all internal links
            internal_links = self.extract_internal_links(content_text, content_path)

            forward_links = []

            # For each link, find the target content and get details
            for link in internal_links:
                target_slug = self._resolve_link_to_slug(link, all_content)
                if target_slug:
                    # Find target content for title
                    target_title = target_slug
                    for content_item in all_content:
                        if content_item.get("slug") == target_slug:
                            target_title = content_item.get("title", target_slug)
                            break

                    # Extract the original link text
                    link_text = self._extract_original_link_text(content_text, link)

                    forward_links.append(
                        {
                            "target_slug": target_slug,
                            "target_title": target_title,
                            "link_text": link_text,
                        }
                    )

            return forward_links

        except Exception as e:
            logger.error(f"Error getting forward links for {source_slug}: {e}")
            return []

    def build_link_graph(self) -> Dict[str, List[str]]:
        """
        Build complete link graph for all content.

        Returns:
            Dict mapping source slugs to lists of target slugs
        """
        if self._is_cache_valid() and self._link_graph_cache:
            return self._link_graph_cache

        link_graph = {}

        try:
            all_content = self._content_provider.get_all_content()

            # Initialize graph with all content
            for content_item in all_content:
                slug = content_item.get("slug", "")
                if slug:
                    link_graph[slug] = []

            # Build links
            for content_item in all_content:
                source_slug = content_item.get("slug", "")
                content_text = content_item.get("content", "")
                content_path = content_item.get("file_path", "")

                if not source_slug:
                    continue

                # Extract all links from this content
                internal_links = self.extract_internal_links(content_text, content_path)

                # Map links to target slugs
                for link in internal_links:
                    target_slug = self._resolve_link_to_slug(link, all_content)
                    if target_slug and target_slug != source_slug:
                        if target_slug not in link_graph[source_slug]:
                            link_graph[source_slug].append(target_slug)

        except Exception as e:
            logger.error(f"Error building link graph: {e}")
            return {}

        # Update cache
        self._link_graph_cache = link_graph
        self._cache_time = datetime.now()

        return link_graph

    def validate_links(self) -> List[Dict[str, str]]:
        """
        Validate all internal links and report broken ones.

        Returns:
            List of dicts with 'source_slug', 'broken_link', 'error'
        """
        broken_links = []

        try:
            all_content = self._content_provider.get_all_content()

            # Create a set of valid slugs for quick lookup
            valid_slugs = {
                content.get("slug", "")
                for content in all_content
                if content.get("slug")
            }

            for content_item in all_content:
                source_slug = content_item.get("slug", "")
                content_text = content_item.get("content", "")
                content_path = content_item.get("file_path", "")

                if not source_slug:
                    continue

                # Extract all internal links
                internal_links = self.extract_internal_links(content_text, content_path)

                for link in internal_links:
                    target_slug = self._resolve_link_to_slug(link, all_content)

                    if not target_slug:
                        broken_links.append(
                            {
                                "source_slug": source_slug,
                                "broken_link": link,
                                "error": "Link target not found",
                            }
                        )
                    elif target_slug not in valid_slugs:
                        broken_links.append(
                            {
                                "source_slug": source_slug,
                                "broken_link": link,
                                "error": f'Target slug "{target_slug}" does not exist',
                            }
                        )

        except Exception as e:
            logger.error(f"Error validating links: {e}")
            return []

        return broken_links

    def get_orphaned_content(self) -> List[str]:
        """
        Find content with no incoming or outgoing links.

        Returns:
            List of content slugs that are orphaned
        """
        try:
            link_graph = self.build_link_graph()

            # Find content with no outgoing links
            no_outgoing = {slug for slug, targets in link_graph.items() if not targets}

            # Find content with no incoming links
            all_targets = set()
            for targets in link_graph.values():
                all_targets.update(targets)

            no_incoming = set(link_graph.keys()) - all_targets

            # Orphaned content has neither incoming nor outgoing links
            orphaned = no_outgoing & no_incoming

            return list(orphaned)

        except Exception as e:
            logger.error(f"Error finding orphaned content: {e}")
            return []

    def refresh_cache(self) -> None:
        """
        Refresh the backlink cache after content changes.
        """
        try:
            self._backlinks_cache.clear()
            self._link_graph_cache = None
            self._cache_time = None

        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")

    def _is_internal_link(self, link: str) -> bool:
        """Check if a link is internal (not external URL)."""
        try:
            parsed = urlparse(link)

            # If it has a scheme and netloc, it's external
            if parsed.scheme and parsed.netloc:
                return False

            # Internal links are relative paths or .md files
            return (
                link.endswith(".md")
                or link.startswith("./")
                or link.startswith("../")
                or link.startswith("notes/")
                or link.startswith("til/")
                or link.startswith("bookmarks/")
                or "://" not in link
            )

        except Exception:
            return True

    def _normalize_link_target(
        self, link_target: str, content_path: str
    ) -> Optional[str]:
        """Normalize a link target to a slug."""
        try:
            # Remove any fragment identifiers
            if "#" in link_target:
                link_target = link_target.split("#")[0]

            # Handle relative paths
            if link_target.startswith("./") or link_target.startswith("../"):
                # Resolve relative to content_path
                content_dir = os.path.dirname(content_path)
                full_path = os.path.normpath(os.path.join(content_dir, link_target))
                link_target = os.path.relpath(full_path)

            # Convert file path to slug
            if link_target.endswith(".md"):
                # Extract filename without extension as slug
                filename = os.path.basename(link_target)
                return filename[:-3]  # Remove .md

            return link_target

        except Exception:
            return None

    def _normalize_wiki_link(self, wiki_link: str) -> Optional[str]:
        """Normalize a wiki-style link to a slug."""
        try:
            # Convert spaces to hyphens and lowercase
            return wiki_link.lower().replace(" ", "-")
        except Exception:
            return None

    def _link_matches_target(self, link: str, target_slug: str) -> bool:
        """Check if a link matches a target slug."""
        try:
            # Direct match
            if link == target_slug:
                return True

            # Case-insensitive match
            if link.lower() == target_slug.lower():
                return True

            # Wiki-style match (spaces to hyphens)
            if link.lower().replace(" ", "-") == target_slug.lower():
                return True

            return False

        except Exception:
            return False

    def _resolve_link_to_slug(
        self, link: str, all_content: List[Dict]
    ) -> Optional[str]:
        """Resolve a link to a content slug."""
        try:
            for content_item in all_content:
                slug = content_item.get("slug", "")
                if self._link_matches_target(link, slug):
                    return slug
            return None
        except Exception:
            return None

    def _extract_link_context(self, content: str, link: str, target_slug: str) -> str:
        """Extract context around a link in content."""
        try:
            # Find the link in content and return surrounding text
            lines = content.split("\n")
            for line in lines:
                if link in line or target_slug in line:
                    return line.strip()[:100]  # Return first 100 chars of line
            return ""
        except Exception:
            return ""

    def _extract_original_link_text(self, content: str, normalized_link: str) -> str:
        """Extract the original link text from content."""
        try:
            # Try to find markdown link that matches
            markdown_matches = self._markdown_link_pattern.findall(content)
            for link_text, link_target in markdown_matches:
                if self._normalize_link_target(link_target, "") == normalized_link:
                    return link_text

            # Try wiki links
            wiki_matches = self._wiki_link_pattern.findall(content)
            for link_target in wiki_matches:
                if self._normalize_wiki_link(link_target) == normalized_link:
                    return link_target

            return normalized_link

        except Exception:
            return normalized_link

    def _is_cache_valid(self) -> bool:
        """Check if the current cache is still valid."""
        try:
            if not self._cache_time:
                return False
            return datetime.now() - self._cache_time < self._cache_ttl
        except Exception:
            return False
