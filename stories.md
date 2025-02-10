# Implementation Plan for Content Models and Search

## 1. Migrate to Anthropic Claude and Enhance AI Features

1. **Update Dependencies and Configuration**
   - [x] Add Anthropic Python client to `pyproject.toml`:
     ```toml
     anthropic = "^0.15.0"  # Latest stable version
     ```
   - [x] Create configuration for Anthropic API:
     ```python
     from anthropic import Anthropic
     
     anthropic = Anthropic()  # Uses ANTHROPIC_API_KEY from env
     ```
   - [x] Update environment setup documentation
   - [x] Add Claude model configuration settings

2. **Enhance Content Analysis with Claude**
   - [x] Update `analyze_content.py`:
     ```python
     # Use Claude for advanced content analysis:
     # - Topic clustering
     # - Content similarity detection
     # - Writing style consistency checks
     # - SEO optimization suggestions
     ```
   - [x] Add content quality metrics
   - [x] Implement content improvement suggestions
   - [x] Add automated content organization recommendations

3. **Improve Metadata Generation**
   - [x] Update `generate_metadata.py` to use Claude:
     ```python
     # Enhanced metadata generation:
     # - More accurate tag suggestions
     # - Better prerequisite identification
     # - Smarter content relationships
     # - Reading time estimation
     # - Content summarization
     ```
   - [x] Add content classification capabilities
   - [x] Implement automated series detection
   - [x] Add content difficulty estimation

4. **Enhanced Content Validation**
   - [ ] Update `validate_frontmatter.py` with Claude:
     ```python
     # Improved validation features:
     # - Content consistency checking
     # - Writing style validation
     # - Link validation and health checks
     # - Image optimization suggestions
     # - Accessibility recommendations
     ```
   - [ ] Add automated content improvement suggestions
   - [ ] Implement content quality scoring
   - [ ] Add SEO optimization checks

5. **Content Migration and Analysis**
   - [ ] Create enhanced content analysis tools:
     ```python
     # Advanced analysis features:
     # - Content structure analysis
     # - Writing style patterns
     # - Topic modeling
     # - Readability metrics
     # - Engagement prediction
     ```

6. **Enhanced Search and Discovery**
   - [ ] Implement semantic search with Claude:
     ```python
     # Advanced search features:
     # - Natural language understanding
     # - Semantic similarity matching
     # - Context-aware results
     # - Multi-modal search (text + code)
     # - Faceted search with dynamic filters
     ```
   - [ ] Add intelligent content organization:
     ```python
     # Smart organization features:
     # - Automated topic clustering
     # - Dynamic content relationships
     # - Learning path generation
     # - Content prerequisite mapping
     ```

7. **AI-Powered Content Recommendations**
   - [ ] Implement smart recommendation engine:
     ```python
     # Advanced recommendation features:
     # - Contextual recommendations
     # - Learning path suggestions
     # - Personalized content discovery
     # - Cross-content type relationships
     # - Engagement optimization
     ```
   - [ ] Add personalization with Claude:
     ```python
     # Enhanced personalization:
     # - User interest modeling
     # - Reading level adaptation
     # - Learning style matching
     # - Progress tracking
     # - Dynamic content paths
     ```

8. **API and Integration Enhancements**
   - [ ] Create enhanced API endpoints:
     ```python
     # New API features:
     # GET /api/search/semantic
     # GET /api/recommend/path
     # GET /api/analyze/content
     # POST /api/generate/metadata
     # Parameters: natural language queries,
     # content types, learning goals
     ```
     # Suggest prerequisites based on content
     # Identify related content through semantic similarity
     # Generate series suggestions for related posts
     # Validate generated metadata
     ```
   - [x] Create front matter validation script:
     ```python
     # Validate against new models
     # Report validation errors
     # Suggest fixes for common issues
     ```
   - [ ] Create migration script:
     ```python
     # Backup original files
     # Process each file:
     #   1. Extract current front matter
     #   2. Get AI suggestions for new metadata
     #   3. Merge existing and new metadata
     #   4. Validate final result
     #   5. Write updated front matter
     # Track changes in a log file
     ```
   - [ ] Add interactive mode:
     ```python
     # Show AI suggestions for each file
     # Allow user to accept/reject/modify suggestions
     # Provide explanation for AI decisions
     # Allow batch approval of similar changes
     ```
   - [ ] Add dry-run option to preview changes
   - [ ] Add rollback capability
   - [ ] Add tests for migration tools
   - [ ] Create metadata enhancement script:
     ```python
     # Periodically analyze content for metadata updates
     # Suggest improvements based on new content
     # Update related_content as new posts are added
     # Maintain content graph relationships
     ```

## Test and Fix Content Management Scripts

1. **Test and Fix Content Analysis Script**
   - [ ] Test `analyze_content.py`:
     ```bash
     # Test on a single file
     uv run python scripts/analyze_content.py --file app/content/notes/2023-09-06-Notes:-Postgres-Database-Scaling-with-Liquibase-on-Kubernetes.md
     
     # Test on all content
     uv run python scripts/analyze_content.py
     ```
   - [ ] Verify:
     - Content quality metrics
     - SEO suggestions
     - Readability scores
     - Content clustering
     - Field usage statistics
     - Missing required fields detection

2. **Test and Fix Metadata Enhancement Script**
   - [ ] Test `enhance_metadata.py`:
     ```bash
     # Test on a single file
     uv run python scripts/enhance_metadata.py --file app/content/notes/2023-09-06-Notes:-Postgres-Database-Scaling-with-Liquibase-on-Kubernetes.md
     
     # Test on all content
     uv run python scripts/enhance_metadata.py
     ```
   - [ ] Verify:
     - Content relationship detection
     - Series grouping suggestions
     - Tag improvements
     - Prerequisites detection
     - Cache functionality
     - Content graph building

3. **Test and Fix Content Migration Script**
   - [ ] Test `migrate_content.py`:
     ```bash
     # Test in dry-run mode on a single file
     uv run python scripts/migrate_content.py --file app/content/notes/2023-09-06-Notes:-Postgres-Database-Scaling-with-Liquibase-on-Kubernetes.md
     
     # Test in interactive mode
     uv run python scripts/migrate_content.py --non-interactive
     
     # Test with changes applied
     uv run python scripts/migrate_content.py --apply
     ```
   - [ ] Verify:
     - Backup creation and restoration
     - Change logging
     - Interactive mode functionality
     - Metadata merging
     - Error handling
     - Rollback capability

4. **Test and Fix Front Matter Validation Script**
   - [ ] Test `validate_frontmatter.py`:
     ```bash
     # Test validation only
     uv run python scripts/validate_frontmatter.py
     
     # Test with auto-fixing
     uv run python scripts/validate_frontmatter.py --fix
     ```
   - [ ] Verify:
     - Model validation
     - Common issue detection
     - Auto-fixing capabilities
     - Error reporting
     - Required field validation
     - Type checking

5. **Test and Fix Metadata Generation Script** ✓
   - [x] Test `generate_metadata.py`:
     ```bash
     # Test on a single file
     uv run python scripts/generate_metadata.py --file app/content/notes/2023-09-06-Notes:-Postgres-Database-Scaling-with-Liquibase-on-Kubernetes.md
     
     # Test with changes applied
     uv run python scripts/generate_metadata.py --file app/content/notes/2023-09-06-Notes:-Postgres-Database-Scaling-with-Liquibase-on-Kubernetes.md --apply
     ```
   - [x] Fixed:
     - File encoding handling
     - Content truncation
     - Metadata preservation
     - Reading time calculation
     - Readability scoring
     - AI integration

6. **Integration Testing**
   - [ ] Test script interactions:
     ```bash
     # Example workflow
     uv run python scripts/validate_frontmatter.py
     uv run python scripts/analyze_content.py
     uv run python scripts/enhance_metadata.py
     uv run python scripts/generate_metadata.py --apply
     ```
   - [ ] Verify:
     - Data consistency across scripts
     - Cache sharing
     - Error propagation
     - Backup management
     - Content integrity

7. **Performance Testing**
   - [ ] Test script performance:
     ```bash
     # Time execution on large content sets
     time uv run python scripts/analyze_content.py
     time uv run python scripts/enhance_metadata.py
     time uv run python scripts/generate_metadata.py
     ```
   - [ ] Monitor:
     - Execution time
     - Memory usage
     - API rate limits
     - Cache effectiveness
     - File I/O performance

8. **Documentation Updates**
   - [ ] Update script documentation:
     - Usage examples
     - Configuration options
     - Error handling
     - Best practices
     - Integration guidelines
   - [ ] Create troubleshooting guide
   - [ ] Document common issues and solutions

9. **Update README with Script Usage Documentation**
   - [ ] Add script workflow section to README:
     ```markdown
     ## Content Management Scripts

     The project includes several scripts for managing content:

     ### 1. Validate Content
     ```bash
     # Check front matter validity
     uv run python scripts/validate_frontmatter.py
     
     # Auto-fix common issues
     uv run python scripts/validate_frontmatter.py --fix
     ```

     ### 2. Analyze Content
     ```bash
     # Analyze a single file
     uv run python scripts/analyze_content.py --file path/to/file.md
     
     # Analyze all content
     uv run python scripts/analyze_content.py
     ```

     ### 3. Generate and Update Metadata
     ```bash
     # Preview metadata changes
     uv run python scripts/generate_metadata.py --file path/to/file.md
     
     # Apply metadata changes
     uv run python scripts/generate_metadata.py --file path/to/file.md --apply
     
     # Enhance existing metadata
     uv run python scripts/enhance_metadata.py
     ```

     ### 4. Migrate Content
     ```bash
     # Preview changes
     uv run python scripts/migrate_content.py
     
     # Apply changes interactively
     uv run python scripts/migrate_content.py --apply
     
     # Apply changes non-interactively
     uv run python scripts/migrate_content.py --apply --non-interactive
     ```

     ### Script Workflow

     1. **New Content**:
        1. Create your markdown file with initial front matter
        2. Run validation to check structure
        3. Generate metadata to enrich content
        4. Analyze content for improvements

     2. **Existing Content**:
        1. Run validation to check for issues
        2. Enhance metadata to update relationships
        3. Analyze content for quality metrics
        4. Generate new metadata if needed

     3. **Bulk Updates**:
        1. Run validation on all content
        2. Use migration script for batch changes
        3. Enhance metadata across all content
        4. Analyze for consistency

     ### Best Practices

     - Always run validation before applying changes
     - Use --apply flag only after previewing changes
     - Keep backups before bulk operations
     - Monitor API usage when running on many files
     - Check logs for errors and warnings
     ```
   - [ ] Add script dependencies section:
     ```markdown
     ### Script Dependencies

     The content management scripts require:
     - Python 3.12+
     - `anthropic` package for AI features
     - `textstat` for readability metrics
     - `rich` for CLI output
     - Environment variables:
       - `ANTHROPIC_API_KEY`
     ```
   - [ ] Add troubleshooting section:
     ```markdown
     ### Common Issues

     1. **API Rate Limits**:
        - Space out bulk operations
        - Use caching for repeated runs
        - Monitor API usage

     2. **File Encoding**:
        - Use UTF-8 for all content
        - Check for BOM markers
        - Verify line endings

     3. **Memory Usage**:
        - Process large sets in batches
        - Clear caches periodically
        - Monitor system resources
     ```

2. **Implement Search Infrastructure**
   - [ ] Add dependencies to `pyproject.toml`:
     ```toml
     whoosh = "^2.7.4"
     ```
   - [ ] Create new file `app/search.py`
   - [ ] Implement `SearchManager` class with schema:
     ```python
     # Fields: path, title, content, tags, created, content_type
     # Add proper analyzers for each field
     # Include docstrings and type hints
     ```
   - [ ] Add index maintenance methods:
     ```python
     # Methods: create_index, rebuild_index, add_document, update_document
     # Include proper error handling
     # Add async support
     ```

## Implement GitHub Actions for Content Automation

1. **Setup Content Validation Workflow**
   - [ ] Create `.github/workflows/validate-content.yml`:
     ```yaml
     # Run on PRs and pushes to main
     name: Validate Content
     on:
       pull_request:
         paths:
           - 'app/content/**'
       push:
         branches: [main]
         paths:
           - 'app/content/**'
     
     jobs:
       validate:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - uses: actions/setup-python@v5
             with:
               python-version: '3.12'
           - name: Install dependencies
             run: |
               python -m pip install --upgrade pip
               pip install -r requirements.txt
           - name: Validate front matter
             run: python scripts/validate_frontmatter.py
           - name: Analyze content
             if: success()
             run: python scripts/analyze_content.py
             env:
               ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
     ```

2. **Setup Metadata Enhancement Workflow**
   - [ ] Create `.github/workflows/enhance-metadata.yml`:
     ```yaml
     name: Enhance Content Metadata
     on:
       schedule:
         - cron: '0 0 * * 0'  # Weekly on Sunday
       workflow_dispatch:  # Manual trigger
     
     jobs:
       enhance:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - uses: actions/setup-python@v5
             with:
               python-version: '3.12'
           - name: Install dependencies
             run: |
               python -m pip install --upgrade pip
               pip install -r requirements.txt
           - name: Enhance metadata
             run: python scripts/enhance_metadata.py
             env:
               ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
           - name: Create Pull Request
             uses: peter-evans/create-pull-request@v6
             with:
               commit-message: 'chore: enhance content metadata'
               title: 'Automated Metadata Enhancement'
               body: |
                 This PR contains automated metadata enhancements:
                 - Updated content relationships
                 - Enhanced tags and categorization
                 - Improved content organization
               branch: metadata-enhancement
               delete-branch: true
     ```

3. **Setup Content Migration Workflow**
   - [ ] Create `.github/workflows/migrate-content.yml`:
     ```yaml
     name: Migrate Content
     on:
       workflow_dispatch:
         inputs:
           dry_run:
             description: 'Run in dry-run mode'
             required: true
             default: 'true'
     
     jobs:
       migrate:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - uses: actions/setup-python@v5
             with:
               python-version: '3.12'
           - name: Install dependencies
             run: |
               python -m pip install --upgrade pip
               pip install -r requirements.txt
           - name: Run migration
             run: |
               if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
                 python scripts/migrate_content.py --non-interactive
               else
                 python scripts/migrate_content.py --non-interactive --apply
               fi
             env:
               ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
     ```

4. **Setup PR Review Workflow**
   - [ ] Create `.github/workflows/pr-review.yml`:
     ```yaml
     name: PR Content Review
     on:
       pull_request:
         paths:
           - 'app/content/**'
     
     jobs:
       review:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - uses: actions/setup-python@v5
             with:
               python-version: '3.12'
           - name: Install dependencies
             run: |
               python -m pip install --upgrade pip
               pip install -r requirements.txt
           - name: Generate metadata
             run: |
               for file in $(git diff --name-only origin/${{ github.base_ref }} | grep '^app/content/.*\.md$'); do
                 python scripts/generate_metadata.py --file "$file" --apply
               done
             env:
               ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
           - name: Create comment
             uses: peter-evans/create-or-update-comment@v4
             with:
               issue-number: ${{ github.event.pull_request.number }}
               body: |
                 Content validation completed:
                 - Front matter validated
                 - Metadata generated
                 - Content analyzed
                 
                 Please review the suggested changes.
     ```

5. **Documentation Updates**
   - [ ] Update README with GitHub Actions workflow documentation
   - [ ] Add troubleshooting guide for CI/CD issues
   - [ ] Document environment variables needed in GitHub Secrets
   - [ ] Add workflow status badges to README

6. **Testing and Refinement**
   - [ ] Test workflows with sample content changes
   - [ ] Verify PR review process
   - [ ] Test metadata enhancement automation
   - [ ] Validate error handling and notifications
   - [ ] Optimize workflow triggers and conditions