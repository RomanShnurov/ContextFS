# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-12-21

### Added

#### Phase 1: Foundation
- Initial MCP server implementation with stdio transport
- Core tools for document access:
  - `list_collections` - Browse folder hierarchy
  - `find_document` - Find documents by name
  - `search_documents` - Full-text search with boolean operators
  - `read_document` - Read document content
- Configuration system with Pydantic validation
- YAML configuration file support
- Environment variable configuration (prefix: `FKM_`)
- CLI entry point with `--root` and `--config` arguments
- Security features:
  - Path validation to prevent directory traversal attacks
  - File access control with symlink policy
  - Filter command security with whitelist/blacklist modes
  - Sandboxed execution for PDF text extraction
- Document format support:
  - PDF (via pdftotext)
  - Markdown (.md, .markdown)
  - Plain text (.txt, .rst)
  - Extensible format system with shell filters
- Search powered by ugrep with:
  - Boolean operators (AND, OR, NOT)
  - Exact phrase matching
  - Context lines around matches
  - Result truncation and limits
- Comprehensive test suite with pytest
- Code quality tools: ruff, mypy
- Project documentation (README, CLAUDE.md)

#### Phase 2: Enhanced Features
- Parallel search with `search_multiple` tool
- Document metadata extraction with `get_document_info` tool
- PDF table of contents extraction
- MCP Resources:
  - `knowledge://index` - Root collection index
  - `knowledge://{path}/index` - Collection index
  - `knowledge://{path}/info` - Document info
- MCP Prompts:
  - `answer_question` - Answer questions using knowledge base
  - `summarize_document` - Summarize a document
  - `compare_documents` - Compare two documents
- Performance improvements:
  - Concurrent search limiting with asyncio.Semaphore
  - Configurable search timeouts
  - Result caching considerations
- Enhanced security:
  - Filter command timeout enforcement
  - Comprehensive security logging
  - Detailed error codes and messages

#### Phase 4: Distribution
- Docker support:
  - Multi-stage Dockerfile for optimized images
  - docker-compose.yaml for easy deployment
  - .dockerignore for clean builds
- PyPI package:
  - Proper pyproject.toml for hatchling build
  - Entry point script configuration
  - Development extras for testing
- GitHub Actions CI/CD:
  - Automated testing on Python 3.12 and 3.13
  - Docker image build and test
  - PyPI publishing on version tags
  - GitHub Container Registry publishing
- Comprehensive documentation:
  - README with quick start and examples
  - Configuration reference (docs/configuration.md)
  - Tools reference (docs/tools.md)
  - Integration guide (docs/integration.md)
  - Cloud sync guide (docs/cloud-sync-guide.md)
- MIT License
- Contributing guidelines

### Design Decisions

#### Phase 3 (Cloud Sync) Intentionally Skipped
Cloud synchronization via rclone has been **intentionally excluded** from this MCP server:

**Rationale:**
- **Security**: Exposing rclone tools to AI clients creates significant risks (data exfiltration, unauthorized cloud access)
- **Single Responsibility**: This is a read-only knowledge base server, not a sync tool
- **Existing Solutions**: Users can use rclone mount, cloud desktop clients, or scheduled sync outside the MCP server
- **Simpler is Better**: Fewer features = smaller attack surface, easier security audits

**Recommended Alternatives:**
- Use `rclone mount` to mount cloud storage as local filesystem
- Use cloud desktop clients (Google Drive, Dropbox, OneDrive)
- Set up scheduled sync via cron/systemd
- See `docs/cloud-sync-guide.md` for detailed integration instructions

### Security

- All file paths validated against knowledge root
- Filter commands validated against whitelist (default mode)
- Shell command execution sandboxed with timeouts
- No write operations supported (read-only by design)
- Symlinks disallowed by default (configurable)
- Comprehensive security error codes and logging

### Dependencies

- Python >= 3.12
- mcp >= 1.0.0
- pydantic >= 2.0
- pydantic-settings >= 2.0
- pypdf >= 4.0
- pyyaml >= 6.0

**System Dependencies:**
- ugrep (search engine)
- poppler-utils (pdftotext for PDF processing)

### Performance

- Concurrent search limiting (default: 4 parallel searches)
- Configurable search timeouts (default: 30s)
- Result truncation (default: 50 results)
- Context line limits (default: 5 lines, max: 50)
- Document read limits (default: 100,000 chars)

## [0.0.1] - 2024-12-18

### Added
- Initial project setup
- Basic project structure
- Development environment configuration

---

## Version History

- **0.1.0** (2024-12-21): First public release with core features, security, and distribution
- **0.0.1** (2024-12-18): Initial project setup

---

## Upgrade Guide

### From 0.0.x to 0.1.0

This is the first public release. No upgrade path needed.

### Configuration Changes

None. First release establishes the configuration schema.

---

## Roadmap

See `specs/improvements-and-suggestions.md` for planned enhancements.

Potential future features:
- Additional document format support (EPUB, DOCX, HTML)
- Advanced search features (regex, proximity search)
- Search result highlighting
- Document preview generation
- Performance optimizations
- Additional MCP resources and prompts

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## Links

- [PyPI Package](https://pypi.org/project/file-knowledge-mcp/)
- [GitHub Repository](https://github.com/yourusername/file-knowledge-mcp)
- [Issue Tracker](https://github.com/yourusername/file-knowledge-mcp/issues)
- [MCP Documentation](https://modelcontextprotocol.io/)
