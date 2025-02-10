#!/usr/bin/env python3
import os
import yaml
import glob
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup
import markdown
import json

CONTENT_DIR = "app/content"
client = OpenAI()

class MetadataGenerator:
    def __init__(self):
        self.md = markdown.Markdown(extensions=['extra'])
    
    def _extract_text_content(self, content: str) -> str:
        """Extract plain text from markdown content."""
        html = self.md.convert(content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    def _get_content_type_prompt(self, content_type: str) -> str:
        """Get type-specific prompt for metadata generation."""
        prompts = {
            'bookmarks': "This is a bookmark entry. Suggest relevant tags and determine its difficulty level for readers.",
            'til': "This is a 'Today I Learned' entry. Identify prerequisites, suggest a difficulty level, and recommend related topics.",
            'notes': "This is a note entry. Identify if it belongs to a series, suggest related content, and determine its evergreen status.",
            'how_to': "This is a how-to guide. Identify prerequisites, determine difficulty level, and suggest related guides.",
            'pages': "This is a static page. Determine its role in the site structure and suggest related content."
        }
        return prompts.get(content_type, "Analyze this content and suggest appropriate metadata.")

    async def generate_metadata(self, file_path: str, content_type: str) -> Dict:
        """Generate metadata for a content file using AI."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split front matter and content if exists
            if content.startswith('---'):
                _, fm, content = content.split('---', 2)
                existing_metadata = yaml.safe_load(fm)
            else:
                existing_metadata = {}
            
            # Extract plain text for AI analysis
            text_content = self._extract_text_content(content)
            
            # Prepare prompt
            prompt = f"""
            {self._get_content_type_prompt(content_type)}
            
            Content:
            {text_content[:1500]}  # Limit content length
            
            Existing metadata:
            {json.dumps(existing_metadata, indent=2)}
            
            Please analyze the content and suggest metadata in the following format:
            1. Difficulty level (beginner/intermediate/advanced)
            2. Prerequisites (if any)
            3. Related topics or content
            4. Appropriate tags
            5. Whether this is evergreen content
            6. If this belongs to a series
            
            Return the response as a JSON object with these fields.
            """
            
            # Call OpenAI API
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a metadata specialist helping to organize technical content."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            suggested_metadata = json.loads(response.choices[0].message.content)
            
            # Merge with existing metadata, preferring existing values
            merged_metadata = {
                **suggested_metadata,
                **existing_metadata,
                "updated": datetime.now().strftime("%Y-%m-%d")
            }
            
            return merged_metadata
            
        except Exception as e:
            print(f"Error generating metadata for {file_path}: {str(e)}")
            return existing_metadata

    async def process_file(self, file_path: str, content_type: str, dry_run: bool = True) -> None:
        """Process a single file, generating and optionally applying metadata."""
        print(f"\nProcessing {file_path}...")
        
        try:
            new_metadata = await self.generate_metadata(file_path, content_type)
            
            if dry_run:
                print("\nSuggested metadata:")
                print(yaml.dump(new_metadata, default_flow_style=False))
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.startswith('---'):
                    _, _, md_content = content.split('---', 2)
                else:
                    md_content = content
                
                # Create new content with updated metadata
                new_content = f"---\n{yaml.dump(new_metadata, default_flow_style=False)}---{md_content}"
                
                # Backup original file
                backup_path = f"{file_path}.bak"
                os.rename(file_path, backup_path)
                
                # Write new content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"Updated {file_path} (backup saved as {backup_path})")
        
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    async def process_all(self, dry_run: bool = True):
        """Process all content files."""
        for content_dir in glob.glob(f"{CONTENT_DIR}/*"):
            if not os.path.isdir(content_dir):
                continue
            
            content_type = os.path.basename(content_dir)
            print(f"\nProcessing {content_type} content...")
            
            for file_path in glob.glob(f"{content_dir}/*.md"):
                await self.process_file(file_path, content_type, dry_run)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate metadata for content files')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    parser.add_argument('--file', help='Process a specific file')
    args = parser.parse_args()
    
    generator = MetadataGenerator()
    
    if args.file:
        content_type = os.path.basename(os.path.dirname(args.file))
        await generator.process_file(args.file, content_type, not args.apply)
    else:
        await generator.process_all(not args.apply)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 