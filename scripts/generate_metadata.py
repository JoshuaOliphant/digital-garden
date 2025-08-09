#!/usr/bin/env python3
import os
import yaml
import glob
from typing import Dict
from datetime import datetime
from anthropic import Anthropic
from bs4 import BeautifulSoup
import markdown
import json
import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import textstat
import shutil
import argparse

from app.config import ai_config

CONTENT_DIR = "app/content"
console = Console()
client = Anthropic(api_key=ai_config.anthropic_api_key)


class MetadataGenerator:
    def __init__(self):
        self.md = markdown.Markdown(extensions=["extra"])

    def _extract_text_content(self, content: str) -> str:
        """Extract plain text from markdown content."""
        html = self.md.convert(content)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def _get_content_type_prompt(self, content_type: str) -> str:
        """Get type-specific prompt for metadata generation."""
        prompts = {
            "bookmarks": """This is a bookmark entry. Please analyze it to:
                1. Suggest relevant tags based on the content and URL
                2. Determine its difficulty level for readers
                3. Identify key topics and themes
                4. Suggest related content categories""",
            "til": """This is a 'Today I Learned' entry. Please analyze it to:
                1. Identify prerequisites and required knowledge
                2. Suggest an appropriate difficulty level
                3. Detect if it belongs to a broader topic series
                4. Recommend related topics for further learning
                5. Estimate reading time and comprehension level""",
            "notes": """This is a note entry. Please analyze it to:
                1. Identify if it belongs to a series or topic collection
                2. Suggest related content and prerequisites
                3. Determine its evergreen status and maintenance needs
                4. Identify key concepts and learning outcomes
                5. Suggest content organization improvements""",
            "how_to": """This is a how-to guide. Please analyze it to:
                1. Identify prerequisites and required knowledge
                2. Determine technical difficulty level
                3. Suggest related guides and resources
                4. Identify key steps and concepts
                5. Recommend improvements for clarity""",
            "pages": """This is a static page. Please analyze it to:
                1. Determine its role in the site structure
                2. Suggest related content and navigation paths
                3. Identify key themes and topics
                4. Recommend content organization improvements""",
        }
        return prompts.get(
            content_type, "Analyze this content and suggest appropriate metadata."
        )

    async def generate_metadata(self, file_path: str, content_type: str) -> Dict:
        """Generate metadata for a content file using Claude."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Split front matter and content if exists
            if content.startswith("---"):
                _, fm, content = content.split("---", 2)
                existing_metadata = yaml.safe_load(fm)
            else:
                existing_metadata = {}

            # Extract plain text for AI analysis
            text_content = self._extract_text_content(content)

            # Calculate reading time and readability metrics
            words = len(text_content.split())
            reading_time = round(words / 200)  # Assuming 200 words per minute
            readability_score = textstat.flesch_reading_ease(text_content)

            # Prepare prompt for Claude
            prompt = f"""
            {self._get_content_type_prompt(content_type)}
            
            Content:
            {text_content[:2000]}  # Limit content length for analysis
            
            Existing metadata:
            {json.dumps(existing_metadata, indent=2)}
            
            Additional metrics:
            - Reading time: {reading_time} minutes
            - Readability score: {readability_score}
            
            Please analyze the content and suggest comprehensive metadata including:
            1. Title optimization (if needed)
            2. Accurate and relevant tags
            3. Difficulty level (beginner/intermediate/advanced)
            4. Prerequisites and required knowledge
            5. Related content suggestions
            6. Series or topic collection membership
            7. Content status (Evergreen/Budding/Archived)
            8. Reading time and comprehension level
            9. Key concepts and learning outcomes
            10. Content organization suggestions
            
            Return the response as a JSON object with these fields.
            """

            # Call Claude API
            message = client.messages.create(
                model=ai_config.claude_model,
                max_tokens=ai_config.claude_max_tokens,
                temperature=ai_config.claude_temperature,
                system=ai_config.system_prompts["metadata"],
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse AI response
            try:
                # Clean the response text to handle potential control characters
                response_text = message.content[0].text.strip()
                response_text = "".join(
                    char for char in response_text if char.isprintable()
                )
                suggested_metadata = json.loads(response_text)

                # Flatten and normalize metadata structure
                flattened_metadata = {
                    "title": suggested_metadata.get(
                        "title", existing_metadata.get("title")
                    ),
                    "created": existing_metadata.get(
                        "created"
                    ),  # Preserve original creation date
                    "updated": datetime.now().strftime("%Y-%m-%d"),
                    "status": suggested_metadata.get(
                        "status", existing_metadata.get("status", "Evergreen")
                    ),
                    "tags": suggested_metadata.get(
                        "tags", existing_metadata.get("tags", [])
                    ),
                    "series": suggested_metadata.get("series", {}).get("name")
                    if isinstance(suggested_metadata.get("series"), dict)
                    else suggested_metadata.get(
                        "series", existing_metadata.get("series")
                    ),
                    "difficulty": suggested_metadata.get(
                        "difficulty",
                        existing_metadata.get("difficulty", "intermediate"),
                    ),
                    "prerequisites": suggested_metadata.get(
                        "prerequisites", existing_metadata.get("prerequisites", [])
                    ),
                    "related_content": suggested_metadata.get(
                        "related_content", existing_metadata.get("related_content", [])
                    ),
                    "reading_time": reading_time,
                    "readability_score": readability_score,
                }

                # Remove None values and empty lists
                merged_metadata = {
                    k: v
                    for k, v in flattened_metadata.items()
                    if v is not None and (not isinstance(v, list) or len(v) > 0)
                }

                return merged_metadata

            except json.JSONDecodeError as e:
                console.print(f"[red]Error parsing Claude response: {str(e)}")
                console.print("[yellow]Falling back to existing metadata")
                return existing_metadata

        except Exception as e:
            console.print(f"[red]Error generating metadata for {file_path}: {str(e)}")
            return existing_metadata

    async def process_file(self, file_path: str, args: argparse.Namespace) -> None:
        try:
            # Read file content in binary mode to handle any encoding issues
            with open(file_path, "rb") as f:
                file_content = f.read().decode("utf-8", errors="replace")

            # Split content into metadata and body
            if file_content.startswith("---\n"):
                _, metadata_str, content = file_content.split("---\n", 2)
                existing_metadata = yaml.safe_load(metadata_str)
            else:
                existing_metadata = {}
                content = file_content

            # Calculate reading time and readability score
            reading_time = calculate_reading_time(content)
            readability_score = round(textstat.flesch_reading_ease(content), 2)

            # Get suggested metadata from AI
            suggested_metadata = await self.generate_metadata(
                file_path, os.path.basename(os.path.dirname(file_path))
            )

            # Flatten and normalize metadata structure
            flattened_metadata = {
                "title": suggested_metadata.get(
                    "title", existing_metadata.get("title")
                ),
                "created": existing_metadata.get(
                    "created"
                ),  # Preserve original creation date
                "updated": datetime.now().strftime("%Y-%m-%d"),
                "status": suggested_metadata.get(
                    "status", existing_metadata.get("status", "Evergreen")
                ),
                "tags": suggested_metadata.get(
                    "tags", existing_metadata.get("tags", [])
                ),
                "series": suggested_metadata.get("series", {}).get("name")
                if isinstance(suggested_metadata.get("series"), dict)
                else suggested_metadata.get("series", existing_metadata.get("series")),
                "difficulty": suggested_metadata.get(
                    "difficulty", existing_metadata.get("difficulty", "intermediate")
                ),
                "prerequisites": suggested_metadata.get(
                    "prerequisites", existing_metadata.get("prerequisites", [])
                ),
                "related_content": suggested_metadata.get(
                    "related_content", existing_metadata.get("related_content", [])
                ),
                "reading_time": reading_time,
                "readability_score": readability_score,
            }

            # Remove None values and empty lists
            merged_metadata = {
                k: v
                for k, v in flattened_metadata.items()
                if v is not None and (not isinstance(v, list) or len(v) > 0)
            }

            # Write the updated content back to the file
            if args.apply:
                # Create a backup of the original file
                backup_path = file_path + ".bak"
                shutil.copy2(file_path, backup_path)

                try:
                    # Write in binary mode to handle any encoding issues
                    with open(file_path, "wb") as f:
                        # Write metadata
                        f.write(b"---\n")
                        yaml_str = yaml.dump(
                            merged_metadata,
                            default_flow_style=False,
                            allow_unicode=True,
                            sort_keys=False,
                        )
                        f.write(yaml_str.encode("utf-8"))
                        f.write(b"---\n")
                        # Write content without any processing
                        f.write(content.rstrip().encode("utf-8"))
                        f.write(b"\n")

                    print(f"Updated {file_path} (backup saved as {backup_path})")
                except Exception as e:
                    # Restore from backup if writing fails
                    shutil.copy2(backup_path, file_path)
                    print(f"Error writing file: {e}. Restored from backup.")
                    raise
            else:
                # Print suggested metadata
                print("\nSuggested metadata:")
                print("---")
                print(
                    yaml.dump(
                        merged_metadata, default_flow_style=False, allow_unicode=True
                    )
                )
                print("---")

        except Exception as e:
            print(f"[red]Error processing {file_path}: {str(e)}")

    async def process_all(self, dry_run: bool = True):
        """Process all content files."""

        # Create a simple namespace object to simulate args
        class Args:
            def __init__(self, apply_changes):
                self.apply = apply_changes

        args = Args(not dry_run)

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
                    f"Processing {content_type} content...", total=None
                )

                for file_path in glob.glob(f"{content_dir}/*.md"):
                    await self.process_file(file_path, args)

                progress.update(task_id, completed=True)


def calculate_reading_time(content: str) -> int:
    """Calculate reading time in minutes based on word count."""
    words = len(content.split())
    # Average reading speed: 200 words per minute
    minutes = max(1, round(words / 200))
    return minutes


async def main():
    parser = argparse.ArgumentParser(description="Generate metadata for content files")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default is dry-run)"
    )
    parser.add_argument("--file", help="Process a specific file")
    args = parser.parse_args()

    generator = MetadataGenerator()

    if args.file:
        await generator.process_file(args.file, args)
    else:
        await generator.process_all(not args.apply)


if __name__ == "__main__":
    asyncio.run(main())
