"""Tests for growth stage migration script."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Add scripts directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from migrate_growth_stages import GrowthStageMigrator
from app.models import GrowthStage


class TestGrowthStageMigration:
    """Test suite for growth stage migration functionality."""
    
    @pytest.fixture
    def temp_content_dir(self):
        """Create temporary content directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content_dir = Path(tmpdir) / "content"
            content_dir.mkdir()
            
            # Create subdirectories
            (content_dir / "notes").mkdir()
            (content_dir / "til").mkdir()
            (content_dir / "bookmarks").mkdir()
            
            yield content_dir
    
    @pytest.fixture
    def migrator(self, temp_content_dir):
        """Create migrator instance with temp directory."""
        return GrowthStageMigrator(temp_content_dir)
    
    def create_test_file(self, dir_path: Path, filename: str, content: str) -> Path:
        """Helper to create test markdown file."""
        file_path = dir_path / filename
        file_path.write_text(content)
        return file_path
    
    def test_parse_frontmatter_with_yaml(self, migrator):
        """Test parsing content with YAML frontmatter."""
        content = """---
title: Test Note
created: "2024-01-01"
tags: [test]
---

This is the content."""
        
        metadata, markdown = migrator.parse_frontmatter(content)
        
        assert metadata["title"] == "Test Note"
        assert metadata["created"] == "2024-01-01"
        assert metadata["tags"] == ["test"]
        assert markdown.strip() == "This is the content."
    
    def test_parse_frontmatter_without_yaml(self, migrator):
        """Test parsing content without frontmatter."""
        content = "Just plain markdown content."
        
        metadata, markdown = migrator.parse_frontmatter(content)
        
        assert metadata == {}
        assert markdown == content
    
    def test_determine_initial_stage_evergreen(self, migrator):
        """Test that Evergreen status maps to evergreen stage."""
        metadata = {"status": "Evergreen"}
        stage = migrator.determine_initial_stage(metadata)
        assert stage == GrowthStage.EVERGREEN.value
    
    def test_determine_initial_stage_budding(self, migrator):
        """Test that Budding status maps to budding stage."""
        metadata = {"status": "Budding"}
        stage = migrator.determine_initial_stage(metadata)
        assert stage == GrowthStage.BUDDING.value
    
    def test_determine_initial_stage_default(self, migrator):
        """Test default stage is seedling."""
        metadata = {"status": "draft"}
        stage = migrator.determine_initial_stage(metadata)
        assert stage == GrowthStage.SEEDLING.value
        
        metadata = {}
        stage = migrator.determine_initial_stage(metadata)
        assert stage == GrowthStage.SEEDLING.value
    
    def test_validate_metadata_valid_note(self, migrator):
        """Test validation of valid note metadata."""
        metadata = {
            "title": "Test Note",
            "created": datetime.now(),
            "updated": datetime.now(),
            "tags": ["test"],
            "growth_stage": "seedling"
        }
        
        is_valid = migrator.validate_metadata(metadata, "notes")
        assert is_valid is True
    
    def test_validate_metadata_invalid(self, migrator):
        """Test validation catches invalid metadata."""
        metadata = {
            "title": "Test Note",
            # Missing required 'created' field
            "tags": ["test"],
            "growth_stage": "invalid_stage"
        }
        
        is_valid = migrator.validate_metadata(metadata, "notes")
        assert is_valid is False
    
    def test_migrate_file_adds_growth_stage(self, migrator, temp_content_dir):
        """Test migrating file adds growth_stage field."""
        content = """---
title: Test Note
created: "2024-01-01"
updated: "2024-01-02"
tags: [test]
status: "Evergreen"
---

Test content."""
        
        file_path = self.create_test_file(
            temp_content_dir / "notes",
            "test.md",
            content
        )
        
        # Run migration
        success = migrator.migrate_file(file_path, dry_run=False)
        assert success is True
        
        # Read updated file
        updated_content = file_path.read_text()
        
        # Parse and check
        metadata, _ = migrator.parse_frontmatter(updated_content)
        assert "growth_stage" in metadata
        assert metadata["growth_stage"] == GrowthStage.EVERGREEN.value
    
    def test_migrate_file_skips_existing_stage(self, migrator, temp_content_dir):
        """Test migration skips files that already have growth_stage."""
        content = """---
title: Test Note
created: "2024-01-01"
tags: [test]
growth_stage: "budding"
---

Test content."""
        
        file_path = self.create_test_file(
            temp_content_dir / "notes",
            "existing.md",
            content
        )
        
        # Run migration
        success = migrator.migrate_file(file_path, dry_run=False)
        assert success is True
        assert migrator.stats["already_has_stage"] == 1
        
        # Verify content unchanged
        updated_content = file_path.read_text()
        metadata, _ = migrator.parse_frontmatter(updated_content)
        assert metadata["growth_stage"] == "budding"
    
    def test_migrate_file_dry_run(self, migrator, temp_content_dir):
        """Test dry run doesn't modify files."""
        original_content = """---
title: Test Note
created: "2024-01-01"
updated: "2024-01-01"
tags: [test]
---

Test content."""
        
        file_path = self.create_test_file(
            temp_content_dir / "notes",
            "dryrun.md",
            original_content
        )
        
        # Run migration in dry run mode
        success = migrator.migrate_file(file_path, dry_run=True)
        assert success is True
        
        # Verify file unchanged
        final_content = file_path.read_text()
        assert final_content == original_content
    
    def test_backup_file(self, migrator, temp_content_dir):
        """Test file backup functionality."""
        content = "Test content"
        file_path = self.create_test_file(
            temp_content_dir / "notes",
            "backup_test.md",
            content
        )
        
        # Create backup
        success = migrator.backup_file(file_path)
        assert success is True
        
        # Check backup exists
        backup_path = migrator.backup_dir / "notes" / "backup_test.md"
        assert backup_path.exists()
        assert backup_path.read_text() == content
    
    def test_migrate_all_processes_multiple_files(self, migrator, temp_content_dir):
        """Test batch migration of multiple files."""
        # Create test files
        files = [
            ("notes", "note1.md", """---
title: Note 1
created: "2024-01-01"
updated: "2024-01-01"
tags: [test]
status: "Evergreen"
---
Content 1"""),
            ("til", "til1.md", """---
title: TIL 1
created: "2024-01-02"
updated: "2024-01-02"
tags: [learning]
---
TIL content"""),
            ("bookmarks", "bookmark1.md", """---
title: Bookmark 1
created: "2024-01-03"
updated: "2024-01-03"
tags: [link]
url: "https://example.com"
---
Bookmark content"""),
        ]
        
        for subdir, filename, content in files:
            self.create_test_file(temp_content_dir / subdir, filename, content)
        
        # Run migration
        migrator.migrate_all(dry_run=False)
        
        # Check stats
        assert migrator.stats["total_files"] == 3
        assert migrator.stats["migrated"] == 3
        assert migrator.stats["already_has_stage"] == 0
        assert len(migrator.stats["errors"]) == 0
        
        # Verify first file got correct stage
        note_path = temp_content_dir / "notes" / "note1.md"
        metadata, _ = migrator.parse_frontmatter(note_path.read_text())
        assert metadata["growth_stage"] == GrowthStage.EVERGREEN.value
        
        # Verify second file got default stage
        til_path = temp_content_dir / "til" / "til1.md"
        metadata, _ = migrator.parse_frontmatter(til_path.read_text())
        assert metadata["growth_stage"] == GrowthStage.SEEDLING.value