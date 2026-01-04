# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-XX

### Added
- Initial release of Fathom MCP
- File-first knowledge base with hierarchical collections
- Full-text search powered by ugrep with boolean operators (AND, OR, NOT)
- Support for multiple document formats (PDF, Markdown, Text, CSV)
- Optional format support (DOCX, ODT, EPUB, HTML, JSON, XML) via external tools
- MCP server implementation with 6 tools:
  - `list_collections` - Browse folder hierarchy
  - `find_document` - Find documents by name
  - `search_documents` - Full-text search with scope control
  - `search_multiple` - Parallel search execution
  - `read_document` - Read document content with page selection
  - `get_document_info` - Get document metadata and TOC
- Security features:
  - Path validation and traversal prevention
  - Shell command sandboxing with whitelist/blacklist modes
  - Read-only design
- Configuration system with YAML and environment variable support
- Docker deployment support with docker-compose
- Claude Desktop integration
- Comprehensive test suite with pytest
- Documentation and examples

### Security
- Implemented defense-in-depth security model
- Path traversal attack prevention
- Command sandboxing with timeout enforcement
- Whitelist-based filter command validation

[Unreleased]: https://github.com/RomanShnurov/fathom-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RomanShnurov/fathom-mcp/releases/tag/v0.1.0
