#!/usr/bin/env python3
import os
import yaml
import glob
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict
from anthropic import AsyncAnthropic
from bs4 import BeautifulSoup
import markdown
import networkx as nx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from scripts.generate_metadata import MetadataGenerator
from app.config import ai_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("metadata_enhancement.log"), logging.StreamHandler()],
)

CONTENT_DIR = "app/content"
CACHE_FILE = "metadata_cache.json"
console = Console()
client = AsyncAnthropic(api_key=ai_config.anthropic_api_key)


class MetadataEnhancer:
    def __init__(self):
        self.metadata_generator = MetadataGenerator()
        self.content_graph = nx.DiGraph()
        self.cache = self._load_cache()
        self.md = markdown.Markdown(extensions=["extra"])

    def _load_cache(self) -> Dict:
        """Load metadata cache from file."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save metadata cache to file."""
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def _extract_text_content(self, content: str) -> str:
        """Extract plain text from markdown content."""
        html = self.md.convert(content)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def _needs_update(self, file_path: str) -> bool:
        """Check if a file needs metadata enhancement."""
        if file_path not in self.cache:
            return True

        last_enhanced = datetime.fromisoformat(self.cache[file_path]["last_enhanced"])
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

        # Update if file was modified or last enhancement was more than 7 days ago
        return file_mtime > last_enhanced or datetime.now() - last_enhanced > timedelta(
            days=7
        )

    def _build_content_graph(self):
        """Build a graph of content relationships."""
        # Clear existing graph
        self.content_graph.clear()

        # Add nodes for all content files
        for content_dir in glob.glob(f"{CONTENT_DIR}/*"):
            if not os.path.isdir(content_dir):
                continue

            content_type = os.path.basename(content_dir)
            for file_path in glob.glob(f"{content_dir}/*.md"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if content.startswith("---"):
                    _, fm, _ = content.split("---", 2)
                    metadata = yaml.safe_load(fm)

                    # Add node with metadata
                    self.content_graph.add_node(
                        file_path, type=content_type, metadata=metadata
                    )

                    # Add edges based on relationships
                    if "related_content" in metadata:
                        for related in metadata["related_content"]:
                            self.content_graph.add_edge(file_path, related)

                    # Add edges based on series
                    if "series" in metadata and metadata["series"]:
                        for other_file in self.content_graph.nodes():
                            other_metadata = self.content_graph.nodes[other_file][
                                "metadata"
                            ]
                            if other_metadata.get("series") == metadata["series"]:
                                self.content_graph.add_edge(file_path, other_file)

    async def _enhance_metadata(self, file_path: str, content_type: str) -> bool:
        """Enhance metadata for a single file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("---"):
                return False

            _, fm, md_content = content.split("---", 2)
            current_metadata = yaml.safe_load(fm)

            # Get related content suggestions
            related_files = []
            if file_path in self.content_graph:
                # Get files with similar tags
                tags = set(current_metadata.get("tags", []))
                for other_file in self.content_graph.nodes():
                    if other_file != file_path:
                        other_metadata = self.content_graph.nodes[other_file][
                            "metadata"
                        ]
                        other_tags = set(other_metadata.get("tags", []))
                        if len(tags & other_tags) >= 2:  # At least 2 common tags
                            related_files.append(other_file)

                # Get files in same series
                if current_metadata.get("series"):
                    for other_file in self.content_graph.nodes():
                        other_metadata = self.content_graph.nodes[other_file][
                            "metadata"
                        ]
                        if other_metadata.get("series") == current_metadata["series"]:
                            related_files.append(other_file)

            # Get AI suggestions for metadata enhancement
            text_content = self._extract_text_content(md_content)
            prompt = f"""
            Analyze this content and its relationships to suggest metadata improvements.
            
            Content:
            {text_content[:1500]}
            
            Current metadata:
            {json.dumps(current_metadata, indent=2)}
            
            Related content files:
            {json.dumps([os.path.basename(f) for f in related_files], indent=2)}
            
            Please suggest improvements for:
            1. Tags (add/remove based on content)
            2. Series grouping
            3. Prerequisites
            4. Difficulty level
            5. Content status (Evergreen/Budding/etc.)
            
            Return suggestions as a JSON object.
            """

            response = await client.messages.create(
                model=ai_config.claude_model,
                max_tokens=ai_config.claude_max_tokens,
                temperature=ai_config.claude_temperature,
                system=ai_config.system_prompts["analysis"],
                messages=[{"role": "user", "content": prompt}],
            )

            suggestions = json.loads(response.content[0].text)

            # Merge suggestions with current metadata
            enhanced_metadata = {
                **current_metadata,
                **suggestions,
                "updated": datetime.now().strftime("%Y-%m-%d"),
            }

            # Update the file
            new_content = f"---\n{yaml.dump(enhanced_metadata, default_flow_style=False)}---{md_content}"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Update cache
            self.cache[file_path] = {
                "last_enhanced": datetime.now().isoformat(),
                "metadata": enhanced_metadata,
            }

            return True

        except Exception as e:
            logging.error(f"Error enhancing metadata for {file_path}: {str(e)}")
            return False

    async def enhance_all(self):
        """Enhance metadata for all content files."""
        try:
            # Build content relationship graph
            self._build_content_graph()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                for content_dir in glob.glob(f"{CONTENT_DIR}/*"):
                    if not os.path.isdir(content_dir):
                        continue

                    content_type = os.path.basename(content_dir)
                    task_id = progress.add_task(
                        f"Enhancing {content_type} content...", total=None
                    )

                    for file_path in glob.glob(f"{content_dir}/*.md"):
                        if self._needs_update(file_path):
                            console.print(f"\nEnhancing {file_path}...")
                            await self._enhance_metadata(file_path, content_type)

                    progress.update(task_id, completed=True)

            # Save cache
            self._save_cache()

            console.print("\n[green]Metadata enhancement completed!")

        except Exception as e:
            logging.error(f"Enhancement failed: {str(e)}")
            raise


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enhance content metadata")
    parser.add_argument("--file", help="Process a specific file")
    args = parser.parse_args()

    enhancer = MetadataEnhancer()

    if args.file:
        content_type = os.path.basename(os.path.dirname(args.file))
        await enhancer._enhance_metadata(args.file, content_type)
    else:
        await enhancer.enhance_all()


if __name__ == "__main__":
    asyncio.run(main())
