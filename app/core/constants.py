"""
Application constants and configuration.
Extracted from main.py to improve modularity.
"""

import bleach

# Directory paths
CONTENT_DIR = "app/content"
TEMPLATE_DIR = "app/templates"
STATIC_DIR = "app/static"

# HTML sanitization configuration
ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p",
    "pre",
    "code",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "ul",
    "ol",
    "li",
    "em",
    "strong",
    "a",
    "img",
    "br",
    "hr",
    "div",
    "span",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "class"],
    "img": ["src", "alt", "title", "width", "height", "class"],
    "div": ["class", "id"],
    "span": ["class", "id"],
    "pre": ["class"],
    "code": ["class"],
    "blockquote": ["class"],
    "table": ["class"],
    "thead": ["class"],
    "tbody": ["class"],
    "tr": ["class"],
    "th": ["class", "scope"],
    "td": ["class"],
    "h1": ["class", "id"],
    "h2": ["class", "id"],
    "h3": ["class", "id"],
    "h4": ["class", "id"],
    "h5": ["class", "id"],
    "h6": ["class", "id"],
    "p": ["class"],
    "ul": ["class"],
    "ol": ["class"],
    "li": ["class"],
}

# GitHub configuration
GITHUB_USERNAME = "JoshuaOliphant"