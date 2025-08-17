"""
ContentManager class for handling content operations in the digital garden.
Extracted from main.py for better code organization.
"""

import os
import re
import random
import yaml
import markdown
import httpx
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict
from pathlib import Path

from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from bs4 import BeautifulSoup
from pydantic import ValidationError
import logging

from app.models import BaseContent, Bookmark, TIL, Note
from app.utils.cache import timed_lru_cache


class ContentManager:
    logger = logging.getLogger(__name__)
    CONTENT_TYPE_MAP = {
        "bookmarks": Bookmark,
        "til": TIL,
        "notes": Note,
        "how_to": Note,  # Using Note model for how-to guides
        "pages": Note,  # Using Note model for pages
    }

    @staticmethod
    def render_markdown(file_path: str) -> dict:
        if not os.path.exists(file_path):
            return {"html": "", "metadata": {}, "errors": ["File not found"]}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML front matter and validate with Pydantic
        metadata, md_content, errors = ContentManager._parse_front_matter(
            content, file_path
        )

        # Convert and sanitize markdown
        html_content = ContentManager._convert_markdown(md_content)
        return {"html": html_content, "metadata": metadata, "errors": errors}

    @staticmethod
    def _parse_front_matter(content: str, file_path: str) -> tuple:
        errors = []
        if content.startswith("---"):
            try:
                _, fm, md_content = content.split("---", 2)
                raw_metadata = yaml.safe_load(fm)

                # Determine content type from file path
                path_parts = file_path.split(os.sep)
                content_type = path_parts[-2] if len(path_parts) > 1 else "notes"

                # Get the appropriate model
                model_class = ContentManager.CONTENT_TYPE_MAP.get(
                    content_type, BaseContent
                )

                try:
                    # Convert string dates to datetime objects
                    if isinstance(raw_metadata.get("created"), str):
                        raw_metadata["created"] = datetime.strptime(
                            raw_metadata["created"], "%Y-%m-%d"
                        )
                    if isinstance(raw_metadata.get("updated"), str):
                        raw_metadata["updated"] = datetime.strptime(
                            raw_metadata["updated"], "%Y-%m-%d"
                        )

                    # Validate with Pydantic model
                    validated_metadata = model_class(**raw_metadata)
                    return validated_metadata.model_dump(), md_content, errors
                except ValidationError as e:
                    errors.extend([f"{err['loc']}: {err['msg']}" for err in e.errors()])
                    return raw_metadata, md_content, errors

            except ValueError:
                errors.append("Invalid front matter format")
                return {}, content, errors
            except yaml.YAMLError as e:
                errors.append(f"YAML parsing error: {str(e)}")
                return {}, content, errors

        errors.append("No front matter found")
        return {}, content, errors

    @staticmethod
    def _convert_markdown(content: str) -> str:
        # Create a custom extension to wrap inline code in spans
        class InlineCodeExtension(markdown.Extension):
            def extendMarkdown(self, md):
                # Override the inline code pattern
                md.inlinePatterns.register(
                    InlineCodePattern(r"(?<!\\)(`+)(.+?)(?<!`)\1(?!`)", md),
                    "backtick",
                    175,
                )

        class InlineCodePattern(markdown.inlinepatterns.Pattern):
            def handleMatch(self, m):
                el = markdown.util.etree.Element("span")
                el.set("class", "inline-code")
                code = markdown.util.etree.SubElement(el, "code")
                code.text = markdown.util.AtomicString(m.group(2))
                return el

        # Custom FencedCode extension to preserve link styling
        class CustomFencedCodeExtension(FencedCodeExtension):
            def extendMarkdown(self, md):
                """Add FencedBlockPreprocessor to the Markdown instance."""
                md.registerExtension(self)
                config = self.getConfigs()
                processor = markdown.extensions.fenced_code.FencedBlockPreprocessor(
                    md, config
                )
                processor.run = lambda lines: self.custom_run(
                    processor, lines
                )  # Override the run method
                md.preprocessors.register(processor, "fenced_code_block", 25)

            def custom_run(self, processor, lines):
                """Custom run method to preserve link styling within code blocks"""
                new_lines = []
                for line in lines:
                    if line.strip().startswith("```"):
                        new_lines.append(line)
                    else:
                        # Replace markdown links with HTML links that have our styling
                        line = re.sub(
                            r"\[(.*?)\]\((.*?)\)",
                            r'<a href="\2" class="text-emerald-600 hover:text-emerald-500 hover:underline">\1</a>',
                            line,
                        )
                        new_lines.append(line)
                return processor.__class__.run(processor, new_lines)

        md = markdown.Markdown(
            extensions=[
                "extra",
                "admonition",
                TocExtension(baselevel=1),
                CustomFencedCodeExtension(),
                InlineCodeExtension(),
            ]
        )

        html_content = md.convert(content)

        # Use BeautifulSoup to modify link styles
        soup = BeautifulSoup(html_content, "html.parser")
        for link in soup.find_all("a"):
            existing_classes = link.get("class", [])
            if isinstance(existing_classes, str):
                existing_classes = existing_classes.split()
            new_classes = existing_classes + [
                "text-emerald-600",
                "hover:text-emerald-500",
                "hover:underline",
            ]
            link["class"] = " ".join(new_classes)

        # Update ALLOWED_ATTRIBUTES to ensure classes survive sanitization
        allowed_attrs = {
            **ALLOWED_ATTRIBUTES,
            "a": ["href", "title", "rel", "class", "target"],
            "iframe": [
                "src",
                "width",
                "height",
                "frameborder",
                "allow",
                "allowfullscreen",
                "title",
                "referrerpolicy",
            ],
        }

        clean_html = bleach.clean(
            str(soup), tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True
        )

        return clean_html

    @staticmethod
    def get_content(content_type: str, limit=None):
        """Get content of a specific type with consistent format"""
        files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        content = []
        validation_errors = {}

        for file in files:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]
            errors = file_content.get("errors", [])

            if errors:
                validation_errors[str(file)] = errors
                # Skip invalid content in production, include with errors in development
                if os.getenv("ENVIRONMENT") == "production":
                    continue

            # Get excerpt
            soup = BeautifulSoup(file_content["html"], "html.parser")
            first_p = soup.find("p")
            excerpt = first_p.get_text() if first_p else ""

            # Create consistent content item structure
            # Convert datetime objects in metadata to strings
            def convert_dates_in_dict(obj):
                if isinstance(obj, dict):
                    return {k: convert_dates_in_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dates_in_dict(item) for item in obj]
                elif isinstance(obj, datetime):
                    return obj.strftime("%Y-%m-%d")
                else:
                    return obj
            
            # Clean metadata of datetime objects
            clean_metadata = convert_dates_in_dict(metadata)
            
            content_item = {
                "name": name,
                "title": clean_metadata.get("title", name.replace("-", " ").title()),
                "created": clean_metadata.get("created", ""),
                "updated": clean_metadata.get("updated", ""),
                "metadata": clean_metadata,
                "excerpt": excerpt,
                "url": f"/{content_type}/{name}",
                "content_type": content_type,
                "type_indicator": {
                    "notes": "Note",
                    "how_to": "How To",
                    "bookmarks": "Bookmark",
                    "til": "TIL",
                }.get(content_type, ""),
                "html": file_content["html"],
            }

            if errors and os.getenv("ENVIRONMENT") != "production":
                content_item["validation_errors"] = errors

            content.append(content_item)

        # Log validation errors
        if validation_errors:
            logfire.warn(
                "content_validation_errors",
                content_type=content_type,
                errors=validation_errors,
            )

        return {
            "content": content[:limit] if limit else content,
            "total": len(content),
            "type": content_type,
        }

    @staticmethod
    def _get_date_from_filename(filename: str | Path) -> str:
        match = re.search(r'(\d{4}-\d{2}-\d{2})', Path(filename).name)
        return match.group(1) if match else '0000-00-00'

    @staticmethod
    def get_random_quote():
        quote_files = list(Path(CONTENT_DIR, "notes").glob("*quoting*.md"))
        if not quote_files:
            return None

        random_quote_file = random.choice(quote_files)
        quote_content = ContentManager.render_markdown(str(random_quote_file))

        # Extract quote safely
        soup = BeautifulSoup(quote_content["html"], "html.parser")
        blockquote = soup.find("blockquote")
        quote_text = blockquote.get_text() if blockquote else ""

        return {
            "text": quote_text,
            "author": quote_content["metadata"].get("author", quote_content["metadata"].get("title", "")),
        }

    @staticmethod
    def get_bookmarks(limit: Optional[int] = 10) -> List[dict]:
        """Get bookmarks with pagination"""
        files = list(Path(CONTENT_DIR, "bookmarks").glob("*.md"))
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)
        bookmarks = []
        files_to_process = (
            files if limit is None else sorted(files, reverse=True)[:limit]
        )

        for file in files_to_process:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]

            # Convert the metadata to a Bookmark model for validation
            try:
                bookmark = Bookmark(**metadata)
                bookmarks.append(
                    {
                        "name": name,
                        "title": bookmark.title,
                        "url": bookmark.url,
                        "created": bookmark.created,
                        "updated": bookmark.updated,
                        "tags": bookmark.tags,
                        "description": bookmark.description,
                        "via_url": bookmark.via_url,
                        "via_title": bookmark.via_title,
                        "commentary": bookmark.commentary,
                        "screenshot_path": bookmark.screenshot_path,
                        "author": bookmark.author,
                        "source": bookmark.source,
                    }
                )
            except ValidationError as e:
                logfire.error(
                    "bookmark_validation_error", bookmark_name=name, error=str(e)
                )
                continue

        return bookmarks

    @staticmethod
    def get_posts_by_tag(tag: str, content_types: List[str] = None):
        posts = []
        if content_types is None:
            content_types = ["notes", "how_to", "til"]

        for content_type in content_types:
            files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
            for file in files:
                name = file.stem
                file_content = ContentManager.render_markdown(str(file))
                metadata = file_content["metadata"]

                if "tags" in metadata and tag in metadata["tags"]:
                    # Get excerpt for all post types
                    soup = BeautifulSoup(file_content["html"], "html.parser")
                    first_p = soup.find("p")
                    excerpt = first_p.get_text() if first_p else ""

                    posts.append(
                        {
                            "type": content_type,
                            "name": name,
                            "title": metadata.get(
                                "title", name.replace("-", " ").title()
                            ),
                            "created": metadata.get("created", ""),
                            "updated": metadata.get("updated", ""),
                            "metadata": metadata,
                            "excerpt": excerpt,
                            "url": f"/{content_type}/{name}",
                        }
                    )

        return sorted(posts, key=lambda x: x.get("created", ""), reverse=True)

    @staticmethod
    @staticmethod
    @timed_lru_cache(maxsize=1, seconds=3600)
    async def get_github_stars(page: int = 1, per_page: int = 30) -> dict:
        """
        Fetch starred GitHub repositories asynchronously with pagination.
        Returns both the stars and pagination info.
        Handles rate limiting gracefully.
        """
        try:
            response = await http_client.get(
                f"https://api.github.com/users/{ai_config.github_username or GITHUB_USERNAME}/starred",
                params={
                    "page": page,
                    "per_page": per_page
                })

            # Handle rate limiting
            if (
                response.status_code == 403
                and "X-RateLimit-Remaining" in response.headers
            ):
                remaining = int(response.headers["X-RateLimit-Remaining"])
                reset_time = int(response.headers["X-RateLimit-Reset"])
                if remaining == 0:
                    reset_datetime = datetime.fromtimestamp(reset_time)
                    logfire.warn(
                        "github_rate_limit_exceeded",
                        reset_time=reset_datetime.isoformat(),
                    )
                    return {
                        "stars": [],
                        "next_page": None,
                        "error": "Rate limit exceeded. Please try again later.",
                    }

            if response.status_code != 200:
                logfire.error(
                    "github_api_error",
                    status_code=response.status_code,
                    response_text=response.text,
                )
                return {
                    "stars": [],
                    "next_page": None,
                    "error": f"GitHub API error: {response.status_code}",
                }

            # Parse Link header for pagination info
            link_header = response.headers.get("Link", "")
            next_page = None
            if link_header:
                links = {}
                for part in link_header.split(","):
                    section = part.split(";")
                    url = section[0].strip()[1:-1]
                    for attr in section[1:]:
                        if "rel=" in attr:
                            rel = attr.split("=")[1].strip('"')
                            links[rel] = url

                if "next" in links:
                    next_page = page + 1

            stars = []
            for repo in response.json():
                stars.append(
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo["description"],
                        "html_url": repo["html_url"],  # Changed from "url" to "html_url"
                        "language": repo["language"],
                        "stargazers_count": repo["stargazers_count"],  # Changed from "stars"
                        "forks_count": repo.get("forks_count", 0),  # Added forks_count
                        "starred_at": datetime.strptime(
                            repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ).strftime("%Y-%m-%d"),
                    }
                )

            return {"stars": stars, "next_page": next_page, "error": None}

        except httpx.RequestError as e:
            logfire.error("github_request_error", error=str(e))
            return {
                "stars": [],
                "next_page": None,
                "error": "Failed to fetch GitHub stars",
            }

    @staticmethod
    def ttl_hash(seconds=3600):
        """Return the same value within `seconds` time period"""
        return round(datetime.now().timestamp() / seconds)
    
    @staticmethod
    def get_tag_counts() -> Dict[str, int]:
        """Get counts of content items by tag."""
        tag_counts = {}
        content_types = ["bookmarks", "til", "notes", "how_to"]
        
        for content_type in content_types:
            files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
            for file in files:
                file_content = ContentManager.render_markdown(str(file))
                metadata = file_content["metadata"]
                for tag in metadata.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return tag_counts
    
    @staticmethod
    def get_topics_data() -> Dict[str, Any]:
        """Get organized topics data with garden bed clustering."""
        from app.config import get_config
        config = get_config()
        
        tag_counts = ContentManager.get_tag_counts()
        garden_beds = config["garden_beds"]
        
        # Organize tags into garden beds
        bed_data = {}
        uncategorized_tags = set(tag_counts.keys())
        
        for bed_name, bed_config in garden_beds.items():
            bed_tags = []
            for tag in bed_config["tags"]:
                if tag in tag_counts:
                    bed_tags.append({
                        "name": tag,
                        "count": tag_counts[tag]
                    })
                    uncategorized_tags.discard(tag)
            
            if bed_tags:
                bed_data[bed_name] = {
                    "tags": sorted(bed_tags, key=lambda x: x["count"], reverse=True),
                    "color": bed_config["color"],
                    "icon": bed_config["icon"],
                    "total_count": sum(tag["count"] for tag in bed_tags)
                }
        
        # Add uncategorized tags if any
        if uncategorized_tags:
            uncategorized = [{
                "name": tag,
                "count": tag_counts[tag]
            } for tag in uncategorized_tags]
            bed_data["Other"] = {
                "tags": sorted(uncategorized, key=lambda x: x["count"], reverse=True),
                "color": "bg-gray-100 text-gray-800 border-gray-200",
                "icon": "🏷️",
                "total_count": sum(tag["count"] for tag in uncategorized)
            }
        
        return bed_data
    
    @staticmethod
    def filter_content_by_tags(selected_tags: List[str]) -> List[Dict[str, Any]]:
        """Filter mixed content by selected tags."""
        if not selected_tags:
            return []
        
        filtered_content = []
        selected_tags_set = set(selected_tags)
        content_types = ["bookmarks", "til", "notes", "how_to"]
        
        for content_type in content_types:
            files = list(Path(CONTENT_DIR, content_type).glob("*.md"))
            for file in files:
                name = file.stem
                file_content = ContentManager.render_markdown(str(file))
                metadata = file_content["metadata"]
                
                # Check if content has any of the selected tags
                if selected_tags_set.intersection(set(metadata.get("tags", []))):
                    # Get excerpt
                    soup = BeautifulSoup(file_content["html"], "html.parser")
                    first_p = soup.find("p")
                    excerpt = first_p.get_text() if first_p else ""
                    
                    filtered_content.append({
                        "type": content_type,
                        "title": metadata.get("title", name.replace("-", " ").title()),
                        "slug": name,
                        "created": metadata.get("created", ""),
                        "updated": metadata.get("updated", ""),
                        "tags": metadata.get("tags", []),
                        "status": metadata.get("status", "Evergreen"),
                        "description": metadata.get("description", excerpt),
                        "url": metadata.get("url", None),
                        "difficulty": metadata.get("difficulty", None)
                    })
        
        # Sort by creation date, newest first
        filtered_content.sort(key=lambda x: x["created"] if x["created"] else "", reverse=True)
        return filtered_content
    
    @staticmethod 
    def get_garden_paths() -> Dict[str, Any]:
        """Get all available garden paths."""
        from app.config import get_config
        config = get_config()
        return config["garden_paths"]
    
    @staticmethod
    def get_garden_path(path_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific garden path by ID."""
        garden_paths = ContentManager.get_garden_paths()
        return garden_paths.get(path_id)
    
    @staticmethod
    def get_path_progress(path_id: str, content_items: List[str]) -> Dict[str, Any]:
        """Calculate progress through a garden path."""
        path_data = ContentManager.get_garden_path(path_id)
        if not path_data:
            return {"progress": 0, "current_step": 0, "total_steps": 0, "completed_items": []}
        
        path_items = path_data["path"]
        completed_items = [item for item in path_items if item in content_items]
        
        return {
            "progress": int((len(completed_items) / len(path_items)) * 100) if path_items else 0,
            "current_step": len(completed_items),
            "total_steps": len(path_items),
            "completed_items": completed_items,
            "next_item": path_items[len(completed_items)] if len(completed_items) < len(path_items) else None
        }
    
    @staticmethod
    def validate_path_content(path_id: str) -> Dict[str, Any]:
        """Validate that all content in a garden path exists."""
        path_data = ContentManager.get_garden_path(path_id)
        if not path_data:
            return {"valid": False, "missing": [], "existing": []}
        
        missing_items = []
        existing_items = []
        
        for item_id in path_data["path"]:
            # Check if content exists in any content type directory
            found = False
            content_types = ["notes", "how_to", "til", "bookmarks"]
            
            for content_type in content_types:
                file_path = Path(CONTENT_DIR, content_type, f"{item_id}.md")
                if file_path.exists():
                    existing_items.append({
                        "id": item_id,
                        "type": content_type,
                        "path": str(file_path)
                    })
                    found = True
                    break
            
            if not found:
                missing_items.append(item_id)
        
        return {
            "valid": len(missing_items) == 0,
            "missing": missing_items,
            "existing": existing_items,
            "path_name": path_data["name"],
            "path_description": path_data["description"]
        }

    @staticmethod
    def get_til_posts(page: int = 1, per_page: int = 30) -> dict:
        """Get TiL posts with pagination"""
        files = list(Path(CONTENT_DIR, "til").glob("*.md"))
        files.sort(key=ContentManager._get_date_from_filename, reverse=True)

        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_files = files[start_idx:end_idx]

        tils = []
        til_tags = {}

        for file in page_files:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]

            # Get first paragraph for excerpt
            soup = BeautifulSoup(file_content["html"], "html.parser")
            first_p = soup.find("p")
            excerpt = first_p.get_text() if first_p else ""

            # Update tag counts
            for tag in metadata.get("tags", []):
                til_tags[tag] = til_tags.get(tag, 0) + 1

            tils.append(
                {
                    "name": name,
                    "title": metadata.get("title", name.replace("-", " ").title()),
                    "created": metadata.get("created", ""),
                    "updated": metadata.get("updated", ""),
                    "tags": metadata.get("tags", []),
                    "status": metadata.get("status", "Evergreen"),
                    "excerpt": excerpt,
                    "url": f"/til/{name}",
                }
            )

        return {
            "tils": tils,
            "til_tags": til_tags,
            "next_page": page + 1 if end_idx < len(files) else None,
        }

    @staticmethod
    def get_til_posts_by_tag(tag: str) -> List[dict]:
        """Get TiL posts filtered by tag"""
        files = list(Path(CONTENT_DIR, "til").glob("*.md"))
        tils = []

        for file in files:
            name = file.stem
            file_content = ContentManager.render_markdown(str(file))
            metadata = file_content["metadata"]

            if tag in metadata.get("tags", []):
                soup = BeautifulSoup(file_content["html"], "html.parser")
                first_p = soup.find("p")
                excerpt = first_p.get_text() if first_p else ""

                tils.append(
                    {
                        "name": name,
                        "title": metadata.get("title", name.replace("-", " ").title()),
                        "created": metadata.get("created", ""),
                        "updated": metadata.get("updated", ""),
                        "tags": metadata.get("tags", []),
                        "status": metadata.get("status", "Evergreen"),
                        "excerpt": excerpt,
                        "url": f"/til/{name}",
                    }
                )

        return sorted(tils, key=lambda x: x["created"], reverse=True)

    @staticmethod
    @timed_lru_cache(maxsize=10, seconds=300)  # Cache for 5 minutes
    async def get_mixed_content(page: int = 1, per_page: int = 10) -> dict:
        """Get mixed content (notes, how-tos, bookmarks, TILs) sorted by date"""
        try:
            all_content = []
            errors = []

            # Get content from different sections
            try:
                notes = ContentManager.get_content("notes")["content"]
            except Exception as e:
                errors.append(f"Error fetching notes: {str(e)}")
                notes = []

            try:
                how_tos = ContentManager.get_content("how_to")["content"]
            except Exception as e:
                errors.append(f"Error fetching how-tos: {str(e)}")
                how_tos = []

            try:
                bookmarks = ContentManager.get_bookmarks()
            except Exception as e:
                errors.append(f"Error fetching bookmarks: {str(e)}")
                bookmarks = []

            try:
                til_result = ContentManager.get_til_posts(page=1, per_page=9999)
                tils = til_result["tils"]
            except Exception as e:
                errors.append(f"Error fetching TILs: {str(e)}")
                tils = []

            # Process and normalize content
            def process_content(items, content_type):
                for item in items:
                    try:
                        # Ensure consistent metadata structure
                        if "metadata" not in item and content_type in [
                            "bookmarks",
                            "til",
                        ]:
                            item["metadata"] = {
                                "title": item.get("title", ""),
                                "created": item.get("created", ""),
                                "updated": item.get("updated", ""),
                                "tags": item.get("tags", []),
                            }

                        # Generate excerpt if not present
                        if "excerpt" not in item and "html" in item:
                            soup = BeautifulSoup(item["html"], "html.parser")
                            first_p = soup.find("p")
                            item["excerpt"] = first_p.get_text() if first_p else ""

                        # Add content type and normalize URL
                        item["content_type"] = content_type
                        if "url" not in item:
                            item["url"] = f"/{content_type}/{item['name']}"

                        # Add type indicator for display
                        item["type_indicator"] = {
                            "notes": "Note",
                            "how_to": "How To",
                            "bookmarks": "Bookmark",
                            "til": "TIL",
                        }.get(content_type, "")

                        all_content.append(item)
                    except Exception as e:
                        errors.append(f"Error processing {content_type} item: {str(e)}")

            # Process each content type
            process_content(notes, "notes")
            process_content(how_tos, "how_to")
            process_content(bookmarks, "bookmarks")
            process_content(tils, "til")

            # Sort all content by date
            def get_date(item):
                # Try different date locations
                date = item.get("created", None)
                if not date:
                    date = item.get("metadata", {}).get("created", None)

                if isinstance(date, str):
                    try:
                        return datetime.strptime(date, "%Y-%m-%d")
                    except ValueError:
                        return datetime.min
                return date or datetime.min

            all_content.sort(key=get_date, reverse=True)

            # Calculate pagination
            if page < 1:
                raise ValueError("Page number must be greater than 0")
            if per_page < 1:
                raise ValueError("Items per page must be greater than 0")

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page

            if start_idx >= len(all_content):
                return {
                    "content": [],
                    "next_page": None,
                    "total": len(all_content),
                    "current_page": page,
                    "total_pages": (len(all_content) + per_page - 1) // per_page,
                    "errors": errors,
                }

            has_more = end_idx < len(all_content)

            return {
                "content": all_content[start_idx:end_idx],
                "next_page": page + 1 if has_more else None,
                "total": len(all_content),
                "current_page": page,
                "total_pages": (len(all_content) + per_page - 1) // per_page,
                "errors": errors,
            }

        except Exception as e:
            raise ValueError(f"Error retrieving mixed content: {str(e)}")
    
    @staticmethod
    def get_all_garden_content() -> Dict[str, Any]:
        """Get all content for the filterable garden homepage."""
        all_content = []
        all_tags = set()
        
        def convert_date_to_string(date_value):
            """Convert datetime objects to strings."""
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d")
            return date_value or ""
        
        # Get content from each type
        notes_result = ContentManager.get_content("notes")
        notes = notes_result["content"] if isinstance(notes_result, dict) else notes_result
        
        how_tos_result = ContentManager.get_content("how_to")
        how_tos = how_tos_result["content"] if isinstance(how_tos_result, dict) else how_tos_result
        
        til_result = ContentManager.get_til_posts(page=1, per_page=9999)
        tils = til_result["tils"]
        
        bookmarks = ContentManager.get_bookmarks(limit=None)
        
        # Process and combine all content
        for note in notes:
            if note.get("metadata", {}).get("status") != "draft":
                note["content_type"] = "notes"
                note["type_label"] = "Note"
                note["growth_stage"] = note.get("metadata", {}).get("status", "Seedling")
                note["tags"] = note.get("metadata", {}).get("tags", [])
                note["created"] = convert_date_to_string(note.get("metadata", {}).get("created", note.get("created", "")))
                note["updated"] = convert_date_to_string(note.get("metadata", {}).get("updated", note.get("updated", "")))
                all_content.append(note)
                all_tags.update(note["tags"])
        
        for how_to in how_tos:
            if how_to.get("metadata", {}).get("status") != "draft":
                how_to["content_type"] = "how_to"
                how_to["type_label"] = "How-To"
                how_to["growth_stage"] = how_to.get("metadata", {}).get("status", "Seedling")
                how_to["tags"] = how_to.get("metadata", {}).get("tags", [])
                how_to["created"] = convert_date_to_string(how_to.get("metadata", {}).get("created", how_to.get("created", "")))
                how_to["updated"] = convert_date_to_string(how_to.get("metadata", {}).get("updated", how_to.get("updated", "")))
                all_content.append(how_to)
                all_tags.update(how_to["tags"])
                
        for til in tils:
            # TILs don't have metadata wrapper, status is at top level
            if til.get("status") != "draft":
                til["content_type"] = "til"
                til["type_label"] = "TIL"
                til["growth_stage"] = til.get("status", "Seedling")
                # Add slug field for TILs
                if 'name' in til and 'slug' not in til:
                    til['slug'] = til['name']
                # Convert dates for TILs
                til["created"] = convert_date_to_string(til.get("created", ""))
                til["updated"] = convert_date_to_string(til.get("updated", ""))
                all_content.append(til)
                all_tags.update(til.get("tags", []))
                
        for bookmark in bookmarks:
            # Bookmarks don't have metadata wrapper, status is at top level
            if bookmark.get("status") != "draft":
                bookmark["content_type"] = "bookmarks"
                bookmark["type_label"] = "Bookmark"
                bookmark["growth_stage"] = bookmark.get("status", "Seedling")
                # Convert dates for bookmarks
                bookmark["created"] = convert_date_to_string(bookmark.get("created", ""))
                bookmark["updated"] = convert_date_to_string(bookmark.get("updated", ""))
                all_content.append(bookmark)
                all_tags.update(bookmark.get("tags", []))
        
        # Sort by creation date (newest first)
        all_content.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        # Get unique growth stages
        growth_stages = list(set(item.get("growth_stage", "Seedling") for item in all_content))
        
        # Get unique content types
        content_types = list(set(item.get("type_label", "") for item in all_content))
        
        return {
            "content": all_content,
            "tags": sorted(list(all_tags)),
            "growth_stages": sorted(growth_stages),
            "content_types": sorted(content_types),
            "total_count": len(all_content)
        }
    
    @staticmethod
    @timed_lru_cache(maxsize=1, seconds=300)
    async def get_homepage_sections() -> Dict[str, Any]:
        """Get structured content sections for the topographical homepage."""
        from collections import defaultdict
        
        # Get all published content
        all_content = []
        
        # Get content from each type
        notes_result = ContentManager.get_content("notes")
        notes = notes_result["content"] if isinstance(notes_result, dict) else notes_result
        
        how_tos_result = ContentManager.get_content("how_to")
        how_tos = how_tos_result["content"] if isinstance(how_tos_result, dict) else how_tos_result
        
        til_result = ContentManager.get_til_posts(page=1, per_page=9999)
        tils = til_result["tils"]
        
        bookmarks = ContentManager.get_bookmarks(limit=None)
        
        # Combine all content
        for note in notes:
            if note.get("status") != "draft":
                note["content_type"] = "notes"
                all_content.append(note)
        
        for how_to in how_tos:
            if how_to.get("status") != "draft":
                how_to["content_type"] = "how_to"
                all_content.append(how_to)
                
        for til in tils:
            if til.get("status") != "draft":
                til["content_type"] = "til"
                all_content.append(til)
                
        for bookmark in bookmarks:
            if bookmark.get("status") != "draft":
                bookmark["content_type"] = "bookmarks"
                all_content.append(bookmark)
        
        sections = {
            'garden_beds': {},
            'recently_tended': [],
            'featured': [],
            'recent_posts': [],
            'github_stars': [],
            'random_quote': None
        }
        
        # Get recent posts (all content sorted by date)
        recent_posts = sorted(
            [item for item in all_content if item.get('status') != 'draft' and item.get('content_type') in ['notes', 'how_to', 'til']],
            key=lambda x: x.get('created', ''),
            reverse=True
        )[:10]  # Get 10 most recent posts
        
        # Add slug field (mapping from name) for template compatibility
        for post in recent_posts:
            if 'name' in post and 'slug' not in post:
                post['slug'] = post['name']
        
        sections['recent_posts'] = recent_posts
        
        # Get GitHub stars (top 5)
        try:
            github_result = await ContentManager.get_github_stars(page=1, per_page=5)
            sections['github_stars'] = github_result.get('stars', [])[:5]
        except Exception:
            sections['github_stars'] = []
        
        # Get random quote
        sections['random_quote'] = ContentManager.get_random_quote()
        
        # Calculate cutoff for recently tended (30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Group content by topics for garden beds
        topic_groups = defaultdict(list)
        
        for item in all_content:
            # Skip draft content
            if item.get('status') == 'draft':
                continue
                
            # Check if recently tended (updated in last 30 days)
            updated_str = item.get('updated', item.get('created', ''))
            if updated_str:
                try:
                    if isinstance(updated_str, str):
                        updated_date = datetime.strptime(updated_str, '%Y-%m-%d')
                    else:
                        updated_date = updated_str
                    if updated_date.replace(tzinfo=None) > thirty_days_ago:
                        sections['recently_tended'].append(item)
                except (ValueError, TypeError, AttributeError):
                    pass
            
            # Group by tags for garden beds
            tags = item.get('tags', [])
            if tags:
                primary_tag = tags[0]  # Use first tag as primary grouping
                topic_groups[primary_tag].append(item)
        
        # Convert topic groups to garden beds
        sections['garden_beds'] = dict(topic_groups)
        
        # Sort recently tended by updated date (most recent first)
        sections['recently_tended'].sort(
            key=lambda x: x.get('updated', x.get('created', '')), 
            reverse=True
        )
        
        # Limit recently tended to reasonable number
        sections['recently_tended'] = sections['recently_tended'][:6]  # Reduced to 6 to make room
        
        # For featured content, take a few high-quality items
        # Priority: Evergreen status, then by creation date
        featured_candidates = [
            item for item in all_content 
            if item.get('status') not in ['draft', 'Budding']
        ]
        featured_candidates.sort(
            key=lambda x: (
                x.get('status') == 'Evergreen',  # Evergreen first
                x.get('created', '')  # Then by date
            ), 
            reverse=True
        )
        sections['featured'] = featured_candidates[:3]  # Top 3
        
        return sections

