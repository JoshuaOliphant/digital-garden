#!/usr/bin/env python3
"""
Migration script to add growth_stage field to existing content.

This script:
1. Scans all markdown files in app/content/
2. Parses existing frontmatter
3. Adds growth_stage field (default: "seedling")
4. Preserves all existing fields
5. Validates the updated content
6. Creates a backup before modifying files
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml
import shutil
from datetime import datetime
import argparse
from pydantic import ValidationError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import BaseContent, Bookmark, TIL, Note, GrowthStage


class GrowthStageMigrator:
    """Handles migration of content files to include growth stage field."""
    
    def __init__(self, content_dir: Path, backup_dir: Optional[Path] = None):
        """Initialize migrator with content directory and optional backup directory.
        
        Args:
            content_dir: Path to content directory
            backup_dir: Optional path for backups (defaults to content_dir.parent / "content_backup")
        """
        self.content_dir = content_dir
        self.backup_dir = backup_dir or content_dir.parent / "content_backup"
        self.stats = {
            "total_files": 0,
            "migrated": 0,
            "already_has_stage": 0,
            "skipped": 0,
            "errors": []
        }
    
    def parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Parse YAML frontmatter from markdown content.
        
        Args:
            content: Raw markdown content
            
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
            
        except yaml.YAMLError as e:
            print(f"  YAML parsing error: {e}")
            return {}, content
    
    def determine_initial_stage(self, metadata: Dict) -> str:
        """Determine appropriate initial growth stage based on content metadata.
        
        Args:
            metadata: Content metadata dictionary
            
        Returns:
            Growth stage value (default: "seedling")
        """
        # If status is Evergreen, start as evergreen
        if metadata.get("status") == "Evergreen":
            return GrowthStage.EVERGREEN.value
        
        # If status is Budding, start as budding
        if metadata.get("status") == "Budding":
            return GrowthStage.BUDDING.value
        
        # Default to seedling for new content
        return GrowthStage.SEEDLING.value
    
    def validate_metadata(self, metadata: Dict, content_type: str) -> bool:
        """Validate metadata against appropriate model.
        
        Args:
            metadata: Content metadata to validate
            content_type: Type of content (notes, til, bookmarks, etc.)
            
        Returns:
            True if valid, False otherwise
        """
        # Map content types to models
        model_map = {
            "bookmarks": Bookmark,
            "til": TIL,
            "notes": Note,
            "how_to": Note,
            "pages": BaseContent,
            "unpublished": BaseContent
        }
        
        model_class = model_map.get(content_type, BaseContent)
        
        try:
            # Try to create model instance for validation
            instance = model_class(**metadata)
            return True
        except ValidationError as e:
            print(f"  Validation error: {e}")
            return False
    
    def backup_file(self, file_path: Path) -> bool:
        """Create backup of file before modification.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            True if backup successful
        """
        try:
            # Create backup directory structure
            relative_path = file_path.relative_to(self.content_dir)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f"  Backup failed: {e}")
            return False
    
    def migrate_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Migrate a single markdown file to include growth stage.
        
        Args:
            file_path: Path to markdown file
            dry_run: If True, don't actually write changes
            
        Returns:
            True if migration successful
        """
        print(f"\nProcessing: {file_path.relative_to(self.content_dir)}")
        
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Parse frontmatter
            metadata, markdown_content = self.parse_frontmatter(content)
            
            # Check if already has growth_stage
            if 'growth_stage' in metadata:
                print("  ✓ Already has growth_stage")
                self.stats["already_has_stage"] += 1
                return True
            
            # Determine initial growth stage
            growth_stage = self.determine_initial_stage(metadata)
            metadata['growth_stage'] = growth_stage
            print(f"  + Adding growth_stage: {growth_stage}")
            
            # Get content type from directory
            content_type = file_path.parent.name
            
            # Validate updated metadata
            if not self.validate_metadata(metadata, content_type):
                print("  ✗ Validation failed, skipping")
                self.stats["errors"].append(str(file_path))
                return False
            
            if not dry_run:
                # Backup original file
                if not self.backup_file(file_path):
                    print("  ✗ Backup failed, skipping")
                    self.stats["errors"].append(str(file_path))
                    return False
                
                # Reconstruct file content
                yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
                new_content = f"---\n{yaml_str}---\n{markdown_content}"
                
                # Write updated content
                file_path.write_text(new_content, encoding='utf-8')
                print("  ✓ File updated")
            else:
                print("  ✓ Would update (dry run)")
            
            self.stats["migrated"] += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.stats["errors"].append(str(file_path))
            return False
    
    def migrate_all(self, dry_run: bool = False) -> None:
        """Migrate all markdown files in content directory.
        
        Args:
            dry_run: If True, don't actually write changes
        """
        print(f"Starting migration of content in: {self.content_dir}")
        if dry_run:
            print("DRY RUN MODE - No files will be modified")
        else:
            print(f"Backup directory: {self.backup_dir}")
        print("-" * 60)
        
        # Find all markdown files
        md_files = list(self.content_dir.rglob("*.md"))
        self.stats["total_files"] = len(md_files)
        
        # Process each file
        for file_path in md_files:
            self.migrate_file(file_path, dry_run)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print migration summary statistics."""
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total files processed: {self.stats['total_files']}")
        print(f"Files migrated: {self.stats['migrated']}")
        print(f"Already had growth_stage: {self.stats['already_has_stage']}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nFiles with errors:")
            for error_file in self.stats['errors']:
                print(f"  - {error_file}")
        
        print("=" * 60)


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate content files to include growth_stage field"
    )
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=Path("app/content"),
        help="Path to content directory (default: app/content)"
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Path to backup directory (default: content_backup)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making actual changes"
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore from backup"
    )
    
    args = parser.parse_args()
    
    # Ensure content directory exists
    if not args.content_dir.exists():
        print(f"Error: Content directory not found: {args.content_dir}")
        sys.exit(1)
    
    if args.restore:
        # Restore from backup
        backup_dir = args.backup_dir or args.content_dir.parent / "content_backup"
        if not backup_dir.exists():
            print(f"Error: Backup directory not found: {backup_dir}")
            sys.exit(1)
        
        print(f"Restoring from backup: {backup_dir}")
        print(f"Target directory: {args.content_dir}")
        
        if input("Are you sure? (y/N): ").lower() != 'y':
            print("Restoration cancelled")
            sys.exit(0)
        
        # Copy backup files back
        shutil.copytree(backup_dir, args.content_dir, dirs_exist_ok=True)
        print("Restoration complete")
    else:
        # Run migration
        migrator = GrowthStageMigrator(args.content_dir, args.backup_dir)
        migrator.migrate_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()