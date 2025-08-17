"""Tags routes with service injection."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.interfaces import IContentProvider
from app.services.dependencies import get_content_service, get_growth_stage_renderer
from app.services.growth_stage_renderer import GrowthStageRenderer
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("app/templates"))
from app.config import get_feature_flags

router = APIRouter()


@router.get("/tags/{tag}", response_class=HTMLResponse)
async def read_tag(
    request: Request,
    tag: str,
    content_service: IContentProvider = Depends(get_content_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer),
):
    """Return posts filtered by tag as an HTMLResponse."""
    template_name = (
        "partials/tag.html"
        if request.headers.get("HX-Request") == "true"
        else "tag.html"
    )

    # Get posts by tag across all content types
    posts_result = content_service.get_posts_by_tag(tag)
    posts = posts_result.get("posts", [])
    total = posts_result.get("total", 0)
    
    # Add growth symbols to each post using the service
    from app.models import GrowthStage
    for post in posts:
        growth_stage_str = post.get("growth_stage", "seedling")
        try:
            growth_stage = GrowthStage(growth_stage_str.lower())
            post["growth_symbol"] = growth_renderer.render_stage_symbol(growth_stage)
            post["growth_css_class"] = growth_renderer.render_stage_css_class(growth_stage)
        except (ValueError, KeyError):
            # Fallback to seedling if invalid stage
            post["growth_symbol"] = growth_renderer.render_stage_symbol(GrowthStage.SEEDLING)
            post["growth_css_class"] = growth_renderer.render_stage_css_class(GrowthStage.SEEDLING)

    # Get tag counts for sidebar
    tag_counts = content_service.get_tag_counts()

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            posts=posts,
            tag=tag,
            total=total,
            tag_counts=tag_counts,
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/topics", response_class=HTMLResponse)
async def read_topics(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer),
):
    """Render the topics/tags overview page as an HTMLResponse."""
    template_name = (
        "partials/topics.html"
        if request.headers.get("HX-Request") == "true"
        else "topics.html"
    )

    # Get all content and tag counts
    all_content = content_service.get_all_content()
    tag_counts = content_service.get_tag_counts()
    
    # Build topics data structure organized by category with icons and colors
    category_config = {
        "programming": {
            "name": "Programming",
            "icon": "💻",
            "color": "text-garden-accent hover:underline",
            "keywords": ["python", "javascript", "rust", "go", "programming", "code", "fastapi", "django", "web", "api", "sql", "github", "gitlab", "docker", "kubernetes", "aws", "terraform", "scripting", "automation", "software", "development", "technical", "ci/cd", "deployment", "configuration", "customization", "databases", "graphql", "interactive", "language", "web-development", "web-hosting", "web-scraping", "zsh", "shell", "command", "cli"]
        },
        "ai-ml": {
            "name": "AI & Machine Learning",
            "icon": "🤖", 
            "color": "text-garden-accent hover:underline",
            "keywords": ["ai", "artificial", "intelligence", "machine", "ml", "chatgpt", "gpt", "openai", "claude", "anthropic", "llm", "ai_engineering", "ai_projects", "innovation", "data", "analytics", "automation"]
        },
        "career": {
            "name": "Career & Work",
            "icon": "💼",
            "color": "text-garden-accent hover:underline", 
            "keywords": ["job_search", "interview", "preparation", "resume", "cv", "career", "work", "business", "insights", "management", "project", "technical", "troubleshooting", "professional", "networking", "maintenance", "job", "interviews", "control", "system", "design"]
        },
        "productivity": {
            "name": "Productivity & Tools",
            "icon": "⚡",
            "color": "text-garden-accent hover:underline",
            "keywords": ["productivity", "tools", "workflow", "organization", "bullet", "journaling", "note", "taking", "time", "management", "efficiency", "features", "focus", "git", "github", "workflow", "simplicity", "reusable", "prompts", "email", "communication", "progress", "bar", "user", "experience"]
        },
        "learning": {
            "name": "Learning & Growth",
            "icon": "📖",
            "color": "text-garden-accent hover:underline",
            "keywords": ["learning", "education", "study", "knowledge", "skill", "development", "reading", "habits", "self", "improvement", "philosophy", "psychology", "thinking", "notes", "documentation", "drafts", "headhunters", "deep", "work", "continuous", "delivery", "branching", "strategies"]
        },
        "tools-apps": {
            "name": "Tools & Applications", 
            "icon": "🛠️",
            "color": "text-garden-accent hover:underline",
            "keywords": ["tools", "applications", "software", "app", "platform", "service", "integration", "slack", "discord", "notion", "obsidian", "chrome", "browser", "extension", "plugin", "artifacts", "avocet", "blog", "post", "caffeine", "alternatives", "code", "examples", "review", "coffee", "interface", "custom", "domain", "dkin", "dns", "configuration", "docker", "e-commerce", "gitflow", "interactive", "json", "fried", "liquidbase", "microservices", "online", "presence", "pipelines", "postgres", "readline", "replit", "routes", "scaling", "shetmet", "slack", "subdomain", "trogon", "tv", "shows", "unix", "website", "workflow"]
        },
        "creative": {
            "name": "Creative & Lifestyle",
            "icon": "🎨",
            "color": "text-garden-accent hover:underline",
            "keywords": ["creativity", "creative", "art", "design", "visual", "drawing", "photography", "music", "writing", "camping", "hiking", "kayaking", "outdoor", "adventure", "travel", "cooking", "baking", "coffee", "lifestyle", "personal", "chaos", "fly", "open", "source", "TIL", "innovation", "letters"]
        },
        "reference": {
            "name": "Reference & Documentation",
            "icon": "📋",
            "color": "text-garden-accent hover:underline",
            "keywords": ["documentation", "reference", "guide", "manual", "cheat", "sheet", "template", "example", "tutorial", "how", "to", "tips", "tricks", "best", "practices", "standards", "format", "schema", "specification", "api", "docs"]
        }
    }
    
    # Categorize tags and build data structure
    topics_data = {}
    all_tags = set()
    
    for tag, count in tag_counts.items():
        all_tags.add(tag)
        
        # Find the best category for this tag
        category = "reference"  # Default fallback category
        tag_lower = tag.lower().replace("_", " ").replace("-", " ")
        
        # Check for exact matches first
        for cat_name, config in category_config.items():
            if tag_lower in config["keywords"]:
                category = cat_name
                break
        
        # If no exact match, check for partial matches
        if category == "reference":
            for cat_name, config in category_config.items():
                for keyword in config["keywords"]:
                    if keyword in tag_lower or tag_lower in keyword:
                        category = cat_name
                        break
                if category != "reference":
                    break
        
        # Initialize category if not exists
        if category not in topics_data:
            config = category_config[category]
            topics_data[category] = {
                "name": config["name"],
                "icon": config["icon"],
                "color": config["color"],
                "tags": [],
                "total_count": 0
            }
        
        # Add tag with count to category
        topics_data[category]["tags"].append({
            "name": tag,
            "count": count
        })
        topics_data[category]["total_count"] += count
    
    # Sort tags within each category by count (descending)
    for category in topics_data:
        topics_data[category]["tags"].sort(key=lambda x: (-x["count"], x["name"]))
    
    # Calculate totals
    total_tags = len(all_tags)
    total_content = len(all_content)

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            topics_data=topics_data,
            total_tags=total_tags,
            total_content=total_content,
            feature_flags=get_feature_flags(),
        )
    )


@router.post("/topics/filter", response_class=HTMLResponse)
async def filter_topics_post(
    request: Request,
    content_service: IContentProvider = Depends(get_content_service),
    growth_renderer: GrowthStageRenderer = Depends(get_growth_stage_renderer),
):
    """Handle POST request for filtering topics."""
    # Get form data
    form_data = await request.form()
    selected_tags = form_data.getlist("tags")
    
    template_name = (
        "partials/topics_filtered.html"
        if request.headers.get("HX-Request") == "true"
        else "topics.html"
    )
    
    if not selected_tags:
        # No tags selected, show empty state
        return HTMLResponse(
            content=env.get_template("partials/topics_filtered.html").render(
                request=request,
                filtered_posts=[],
                selected_tags=[],
                total_results=0,
                feature_flags=get_feature_flags(),
            )
        )
    
    # Get posts that have ALL selected tags (intersection)
    all_content = content_service.get_all_content()
    filtered_posts = []
    
    for post in all_content:
        post_tags = post.get("tags", [])
        # Check if post has all selected tags
        if all(tag in post_tags for tag in selected_tags):
            filtered_posts.append(post)
    
    # Add growth symbols to filtered posts using the service
    from app.models import GrowthStage
    for post in filtered_posts:
        growth_stage_str = post.get("growth_stage", "seedling")
        try:
            growth_stage = GrowthStage(growth_stage_str.lower())
            post["growth_symbol"] = growth_renderer.render_stage_symbol(growth_stage)
            post["growth_css_class"] = growth_renderer.render_stage_css_class(growth_stage)
        except (ValueError, KeyError):
            # Fallback to seedling if invalid stage
            post["growth_symbol"] = growth_renderer.render_stage_symbol(GrowthStage.SEEDLING)
            post["growth_css_class"] = growth_renderer.render_stage_css_class(GrowthStage.SEEDLING)
    
    return HTMLResponse(
        content=env.get_template("partials/topics_filtered.html").render(
            request=request,
            filtered_posts=filtered_posts,
            selected_tags=selected_tags,
            total_results=len(filtered_posts),
            feature_flags=get_feature_flags(),
        )
    )


@router.get("/topics/filter", response_class=HTMLResponse)
async def filter_topics_get(
    request: Request,
    content_type: str = None,
    min_count: int = 1,
    content_service: IContentProvider = Depends(get_content_service),
):
    """Handle GET request for filtering topics with query parameters."""
    template_name = (
        "partials/topics_filtered.html"
        if request.headers.get("HX-Request") == "true"
        else "topics.html"
    )

    # Get all tag counts
    tag_counts = content_service.get_tag_counts()

    # Apply filters
    filtered_tags = {
        tag: count for tag, count in tag_counts.items() if count >= min_count
    }

    # If content_type filter is specified, filter further
    if content_type:
        # This would require additional logic in ContentService
        # to get tags by content type
        pass

    # Sort tags by count (descending) and then alphabetically
    sorted_tags = sorted(filtered_tags.items(), key=lambda x: (-x[1], x[0]))

    return HTMLResponse(
        content=env.get_template(template_name).render(
            request=request,
            tag_counts=sorted_tags,
            total_tags=len(sorted_tags),
            content_type=content_type,
            min_count=min_count,
            feature_flags=get_feature_flags(),
        )
    )
