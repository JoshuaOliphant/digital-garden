# Digital Garden

A digital garden for organizing and sharing knowledge, powered by FastAPI and AI.

## Features

- Content management with Markdown and YAML front matter
- AI-powered metadata generation and content analysis
- Automatic content relationships and recommendations
- Search with semantic understanding
- Beautiful, responsive UI

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/digital_garden.git
   cd digital_garden
   ```

2. Create a Python virtual environment (Python 3.12+ required):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with:
   ```env
   # Required API keys
   ANTHROPIC_API_KEY=your_anthropic_api_key
   OPENAI_API_KEY=your_openai_api_key

   # Optional settings
   ENVIRONMENT=development  # or production
   CLAUDE_MODEL=claude-3-sonnet-20240229  # or other model version
   CLAUDE_MAX_TOKENS=4096
   CLAUDE_TEMPERATURE=0.7
   ```

5. Initialize the content directories:
   ```bash
   python -c "from app.config import setup_directories; setup_directories()"
   ```

6. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The site will be available at `http://localhost:8000`

## Content Structure

Content is organized in the following directories under `app/content/`:
- `bookmarks/`: Links to interesting resources
- `how_to/`: Step-by-step guides
- `notes/`: General notes and articles
- `pages/`: Static pages (about, now, etc.)
- `til/`: Today I Learned snippets

Each content file should be a Markdown file with YAML front matter:
```markdown
---
title: "Your Title Here"
created: "2024-03-14"
updated: "2024-03-14"
tags: [tag1, tag2]
status: "Evergreen"  # or "Budding"
---

Your content here...
```

## AI Features

The site uses AI (Claude and GPT-4) for:
- Metadata generation and enhancement
- Content analysis and recommendations
- Semantic search
- Writing style consistency
- SEO optimization

Configure AI behavior in `app/config.py`

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black .
```

Type checking:
```bash
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
