#!/usr/bin/env python3
import os
import yaml
import glob
import shutil
import logging
from datetime import datetime
from typing import Dict
import asyncio
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from scripts.generate_metadata import MetadataGenerator
from scripts.validate_frontmatter import FrontMatterValidator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("content_migration.log"), logging.StreamHandler()],
)

CONTENT_DIR = "app/content"
BACKUP_DIR = "app/content_backup"
console = Console()


class ContentMigrator:
    def __init__(self, interactive: bool = True, dry_run: bool = True):
        self.interactive = interactive
        self.dry_run = dry_run
        self.metadata_generator = MetadataGenerator()
        self.validator = FrontMatterValidator()
        self.changes_log = []

    def _create_backup(self):
        """Create a backup of all content files."""
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(CONTENT_DIR, BACKUP_DIR)
        logging.info(f"Created backup in {BACKUP_DIR}")

    def _restore_backup(self):
        """Restore content from backup."""
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(CONTENT_DIR)
            shutil.copytree(BACKUP_DIR, CONTENT_DIR)
            logging.info("Restored content from backup")
        else:
            logging.error("No backup found to restore")

    def _log_change(self, file_path: str, change_type: str, details: str):
        """Log a content change."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.changes_log.append(
            {
                "timestamp": timestamp,
                "file": file_path,
                "type": change_type,
                "details": details,
            }
        )
        logging.info(f"{change_type}: {file_path} - {details}")

    def _display_changes(self, old_metadata: Dict, new_metadata: Dict) -> bool:
        """Display metadata changes and get user approval."""
        if not self.interactive:
            return True

        table = Table(title="Metadata Changes")
        table.add_column("Field")
        table.add_column("Old Value")
        table.add_column("New Value")

        all_keys = set(old_metadata.keys()) | set(new_metadata.keys())
        has_changes = False

        for key in sorted(all_keys):
            old_val = old_metadata.get(key, "")
            new_val = new_metadata.get(key, "")
            if old_val != new_val:
                has_changes = True
                table.add_row(key, str(old_val), str(new_val))

        if has_changes:
            console.print(table)
            return Confirm.ask("Apply these changes?")
        return True

    async def _process_file(self, file_path: str, content_type: str) -> bool:
        """Process a single content file."""
        try:
            # Read current content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract current metadata
            current_metadata = {}
            if content.startswith("---"):
                _, fm, md_content = content.split("---", 2)
                current_metadata = yaml.safe_load(fm)
            else:
                md_content = content

            # Generate new metadata
            new_metadata = await self.metadata_generator.generate_metadata(
                file_path, content_type
            )

            # Validate new metadata
            valid, errors = self.validator.validate_file(file_path, content_type)
            if not valid:
                if self.interactive:
                    console.print(f"[red]Validation errors in {file_path}:")
                    for error in errors:
                        console.print(f"  ✗ {error}")
                    if not Confirm.ask("Continue with invalid metadata?"):
                        return False

            # Get approval for changes
            if not self._display_changes(current_metadata, new_metadata):
                return False

            if not self.dry_run:
                # Create new content with updated metadata
                new_content = f"---\n{yaml.dump(new_metadata, default_flow_style=False)}---{md_content}"

                # Write updated content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                self._log_change(file_path, "UPDATE", "Updated metadata")

            return True

        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
            return False

    async def migrate_all(self):
        """Migrate all content files."""
        try:
            # Create backup
            if not self.dry_run:
                self._create_backup()

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
                        if self.interactive:
                            console.print(f"\nProcessing {file_path}...")

                        success = await self._process_file(file_path, content_type)
                        if not success and self.interactive:
                            if not Confirm.ask("Continue with next file?"):
                                if not self.dry_run:
                                    self._restore_backup()
                                return

                    progress.update(task_id, completed=True)

            # Write change log
            log_path = "content_migration.json"
            import json

            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(self.changes_log, f, indent=2)

            if not self.dry_run:
                console.print(
                    f"\n[green]Migration completed! Changes logged to {log_path}"
                )
            else:
                console.print("\n[yellow]Dry run completed. No changes were made.")

        except Exception as e:
            logging.error(f"Migration failed: {str(e)}")
            if not self.dry_run:
                self._restore_backup()
            raise


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migrate content files")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default is dry-run)"
    )
    parser.add_argument(
        "--non-interactive", action="store_true", help="Run without user interaction"
    )
    parser.add_argument("--file", help="Process a specific file")
    args = parser.parse_args()

    migrator = ContentMigrator(
        interactive=not args.non_interactive, dry_run=not args.apply
    )

    if args.file:
        content_type = os.path.basename(os.path.dirname(args.file))
        await migrator._process_file(args.file, content_type)
    else:
        await migrator.migrate_all()


if __name__ == "__main__":
    asyncio.run(main())
