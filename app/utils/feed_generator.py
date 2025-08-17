"""RSS feed and sitemap generation utilities."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from email.utils import format_datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

from app.interfaces import IContentProvider


def generate_rss_feed(content_service: IContentProvider, growth_stage: Optional[str] = None) -> str:
    """Generate RSS feed XML from content service.
    
    Args:
        content_service: The content provider service
        growth_stage: Optional filter by growth stage (seedling, budding, growing, evergreen)
    """
    # Get all content from service
    posts = content_service.get_all_content()
    
    # Filter out drafts and sort by date
    published_posts = [p for p in posts if p.get("status") != "draft"]
    
    # Filter by growth stage if specified
    if growth_stage:
        valid_stages = ["seedling", "budding", "growing", "evergreen"]
        if growth_stage.lower() in valid_stages:
            published_posts = [p for p in published_posts if p.get("growth_stage", "seedling").lower() == growth_stage.lower()]
    
    # Sort by date with proper type handling
    def get_sort_key(item):
        created = item.get("created", "")
        if isinstance(created, str):
            return created
        if hasattr(created, 'isoformat'):
            return created.isoformat()
        return str(created)
    
    published_posts.sort(key=get_sort_key, reverse=True)
    
    base_url = "https://joshuaoliph.com"
    title = "Joshua Oliphant's Digital Garden"
    description = "A digital garden of ideas, notes, and learnings"
    
    # Create RSS root element
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    # Add channel metadata
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = base_url
    ET.SubElement(channel, "description").text = description
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now())
    
    # Add items
    for post in published_posts[:20]:  # Limit to 20 most recent items
        item = ET.SubElement(channel, "item")
        
        # Title
        ET.SubElement(item, "title").text = post.get("title", "Untitled")
        
        # Link
        content_type = post.get("content_type", "notes")
        slug = post.get("slug", post.get("name", ""))
        ET.SubElement(item, "link").text = f"{base_url}/{content_type}/{slug}"
        
        # Description with growth stage info
        description = post.get("description", "")
        if not description and "html" in post:
            # Extract first paragraph from HTML
            import re
            match = re.search(r'<p>(.*?)</p>', post["html"])
            if match:
                description = match.group(1)
        
        # Add growth stage information to description
        growth_stage = post.get("growth_stage", "seedling")
        growth_indicator = {
            "seedling": "🌱 Seedling",
            "budding": "🌿 Budding", 
            "growing": "🌳 Growing",
            "evergreen": "🌲 Evergreen"
        }.get(growth_stage.lower(), "🌱 Seedling")
        
        if description:
            description = f"[{growth_indicator}] {description}"
        else:
            description = f"[{growth_indicator}] {post.get('title', 'Untitled')}"
            
        ET.SubElement(item, "description").text = description
        
        # Publication date - handle multiple date formats
        pub_date = post.get("created", datetime.now())
        
        # Convert to datetime object if needed
        if isinstance(pub_date, str):
            try:
                # Try standard ISO format first
                pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except ValueError:
                try:
                    # Try simple date format like "2025-1-14"
                    pub_date = datetime.strptime(pub_date, "%Y-%m-%d")
                except ValueError:
                    # Fallback to current date
                    pub_date = datetime.now()
        elif hasattr(pub_date, 'date') and not hasattr(pub_date, 'time'):
            # Handle datetime.date objects by converting to datetime
            from datetime import time
            pub_date = datetime.combine(pub_date, time.min)
        elif not isinstance(pub_date, datetime):
            # Fallback for any other type
            pub_date = datetime.now()
            
        ET.SubElement(item, "pubDate").text = format_datetime(pub_date)
        
        # GUID
        ET.SubElement(item, "guid").text = f"{base_url}/{content_type}/{slug}"
        
        # Categories (tags)
        for tag in post.get("tags", []):
            ET.SubElement(item, "category").text = tag
    
    # Convert to string with pretty printing
    xml_str = ET.tostring(rss, encoding="unicode")
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ")


def generate_sitemap(content_service: IContentProvider) -> str:
    """Generate XML sitemap from content service."""
    # Get all content from service
    content_items = content_service.get_all_content()
    
    base_url = "https://joshuaoliph.com"
    static_pages = ["/", "/now", "/projects", "/bookmarks", "/til", "/garden", "/explore", "/topics"]
    
    # Create sitemap root
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Add static pages
    for page in static_pages:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = f"{base_url}{page}"
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "0.8" if page == "/" else "0.7"
    
    # Add content items
    for item in content_items:
        # Only include published content
        if item.get("status") in ["Evergreen", "Budding", None]:
            url = ET.SubElement(urlset, "url")
            
            content_type = item.get("content_type", "notes")
            slug = item.get("slug", item.get("name", ""))
            ET.SubElement(url, "loc").text = f"{base_url}/{content_type}/{slug}"
            
            # Last modified date
            updated = item.get("updated") or item.get("created")
            if updated:
                if isinstance(updated, str):
                    updated = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                ET.SubElement(url, "lastmod").text = updated.strftime("%Y-%m-%d")
            
            # Change frequency based on growth stage
            growth_stage = item.get("growth_stage", "seedling")
            if growth_stage == "evergreen":
                changefreq = "monthly"
            elif growth_stage in ["growing", "budding"]:
                changefreq = "weekly"
            else:
                changefreq = "daily"
            ET.SubElement(url, "changefreq").text = changefreq
            
            # Priority based on content type and growth stage
            if content_type == "notes" and growth_stage == "evergreen":
                priority = "0.9"
            elif content_type == "notes":
                priority = "0.7"
            else:
                priority = "0.6"
            ET.SubElement(url, "priority").text = priority
    
    # Convert to string with XML declaration
    xml_str = ET.tostring(urlset, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'