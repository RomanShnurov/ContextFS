# file-knowledge-mcp

[![PyPI version](https://badge.fury.io/py/file-knowledge-mcp.svg)](https://pypi.org/project/file-knowledge-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

File-first knowledge base MCP server. Search your documents with AI using the Model Context Protocol.

## Features

- **File-first approach** - Search directly in files using ugrep (no database/RAG required)
- **Boolean search** - AND, OR, NOT operators for precise queries
- **Hierarchical collections** - Organize documents in folders
- **Multiple formats** - PDF, Markdown, plain text, and more
- **Security-first** - Path validation, command sandboxing, read-only by design
- **Parallel search** - Search multiple terms simultaneously for faster results
- **Document metadata** - Get table of contents and metadata information

## Quick Start

### Installation

```bash
# Install from PyPI
pip install file-knowledge-mcp
```

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt install ugrep poppler-utils

# macOS
brew install ugrep poppler
```

### Usage

```bash
# Start with a documents folder
file-knowledge-mcp --root ./my-documents

# Or with a config file
file-knowledge-mcp --config config.yaml
```

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "knowledge": {
      "command": "file-knowledge-mcp",
      "args": ["--root", "/path/to/documents"]
    }
  }
}
```

On macOS, the config file is typically located at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

On Windows:
`%APPDATA%/Claude/claude_desktop_config.json`

Restart Claude Desktop after making changes.

## Configuration

Create a `config.yaml`:

```yaml
knowledge:
  root: "./documents"

search:
  context_lines: 5
  max_results: 50
  timeout: 30

security:
  enable_shell_filters: true
  filter_mode: whitelist

exclude:
  patterns:
    - ".git/*"
    - "*.draft.*"
```

See [config.example.yaml](config.example.yaml) for all options.

### Environment Variables

All configuration options can be set via environment variables with the `FKM_` prefix:

```bash
export FKM_KNOWLEDGE__ROOT=/path/to/documents
export FKM_SEARCH__MAX_RESULTS=100
export FKM_SECURITY__FILTER_MODE=whitelist
```

## Tools

| Tool | Description |
|------|-------------|
| `list_collections` | Browse document folders |
| `find_document` | Find documents by name |
| `search_documents` | Search inside documents |
| `search_multiple` | Parallel search for multiple terms |
| `read_document` | Read document content |
| `get_document_info` | Get metadata and TOC |

### list_collections

Browse the folder structure of your knowledge base.

```json
{
  "path": "programming/python"
}
```

Returns a list of collections (folders) and documents in the specified path.

### find_document

Find documents by name or path pattern.

```json
{
  "query": "async",
  "limit": 10
}
```

### search_documents

Full-text search with boolean operators and scope control.

```json
{
  "query": "authentication jwt",
  "scope": {
    "type": "global"
  }
}
```

Scope types:
- `global` - Search all documents
- `collection` - Search within a specific folder
- `document` - Search within a single document

### Search Syntax

```
"attack armor"     - Find both terms (AND)
"move|teleport"    - Find either term (OR)
"attack -ranged"   - Exclude term (NOT)
'"end of turn"'    - Exact phrase
```

### search_multiple

Search for multiple queries in parallel for faster results.

```json
{
  "queries": ["authentication", "authorization", "security"],
  "scope": {
    "type": "collection",
    "path": "docs/api"
  }
}
```

### read_document

Read the full content of a document.

```json
{
  "path": "guides/tutorial.pdf",
  "pages": [1, 2, 3]
}
```

For PDFs, you can optionally specify which pages to read. Omit `pages` to read the entire document.

### get_document_info

Get metadata and table of contents for a document.

```json
{
  "path": "guides/manual.pdf"
}
```

Returns information like page count, file size, format, and extracted table of contents (for PDFs).

## Docker

### Build and Run

```bash
# Build
docker build -t file-knowledge-mcp .

# Run (read-only mount recommended)
docker run -v ./docs:/knowledge:ro file-knowledge-mcp

# With custom config
docker run -v ./docs:/knowledge:ro -v ./config.yaml:/config/config.yaml:ro file-knowledge-mcp
```

### Using docker-compose

```bash
# Start
docker-compose up

# Build and start
docker-compose up --build

# Run in background
docker-compose up -d
```

The `docker-compose.yaml` file includes:
- Read-only document mounting for security
- Resource limits (512MB memory, 1 CPU)
- Proper stdio configuration for MCP communication

## Cloud Storage Integration

This server provides read-only access to your local knowledge base. If you need to sync documents from cloud storage, use one of these approaches:

### Option 1: rclone mount (Recommended)

Mount cloud storage as a local directory that the MCP server can read:

```bash
# Mount Google Drive as local directory
rclone mount gdrive:Knowledge /data/knowledge --read-only --vfs-cache-mode full

# Mount in background with logging
rclone mount gdrive:Knowledge /data/knowledge \
  --read-only \
  --vfs-cache-mode full \
  --log-file=/var/log/rclone.log \
  --daemon
```

Then configure the MCP server to use the mount point:

```yaml
knowledge:
  root: "/data/knowledge"
```

### Option 2: Cloud Desktop Clients

Use official sync clients to automatically sync files to a local folder:

- **Google Drive Desktop** - Syncs Google Drive to your computer
- **Dropbox** - Syncs Dropbox folders
- **OneDrive** - Syncs OneDrive/SharePoint
- **iCloud Drive** - Syncs iCloud documents

Point the MCP server at the synced folder:

```yaml
knowledge:
  root: "~/Google Drive/Knowledge"
```

### Option 3: Scheduled Sync

Set up periodic sync with cron/systemd:

```bash
# Example cron job (sync every 30 minutes)
*/30 * * * * rclone sync gdrive:Knowledge /data/knowledge --log-file=/var/log/rclone-sync.log
```

Or use a systemd timer for more control. See `docs/cloud-sync-guide.md` for detailed setup instructions.

### Why Not Built-in Sync?

Cloud sync is intentionally kept separate from the MCP server for:

- **Security** - Prevents AI from accessing cloud credentials or triggering syncs
- **Single Responsibility** - Server focuses on read-only document access
- **Flexibility** - Use any sync method that works for your setup
- **Simplicity** - Smaller attack surface, easier security audits

## Development

### Setup

```bash
# Clone
git clone https://github.com/yourusername/file-knowledge-mcp
cd file-knowledge-mcp

# Install with dev dependencies
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_search.py

# Run specific test
uv run pytest tests/test_search.py::test_search_simple_query
```

### Code Quality

```bash
# Lint and format
uv run ruff check src tests
uv run ruff format src tests

# Type checking
uv run mypy src
```

### Project Structure

```
file-knowledge-mcp/
├── src/file_knowledge_mcp/
│   ├── config.py          # Configuration management
│   ├── errors.py          # Error definitions
│   ├── security.py        # Security controls
│   ├── server.py          # MCP server
│   ├── __main__.py        # CLI entry point
│   ├── tools/
│   │   ├── browse.py      # list_collections, find_document
│   │   ├── search.py      # search_documents, search_multiple
│   │   └── read.py        # read_document, get_document_info
│   └── search/
│       └── ugrep.py       # Search engine wrapper
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_browse.py
│   ├── test_search.py
│   └── test_read.py
├── docs/
│   └── cloud-sync-guide.md  # Cloud storage integration guide
├── specs/
│   ├── phase-1-foundation.md
│   ├── phase-2-enhancements.md
│   └── phase-4-distribution.md
├── Dockerfile
├── docker-compose.yaml
├── pyproject.toml
└── config.example.yaml
```

## Security

This server implements multiple security layers:

- **Path Validation** - All file paths validated to prevent directory traversal
- **Command Sandboxing** - Shell commands (PDF filters) run in restricted mode
- **Read-Only** - Server never writes to the knowledge base
- **Whitelist Mode** - Filter commands validated against whitelist
- **Timeout Protection** - All operations have configurable timeouts
- **No Cloud Credentials** - Server never accesses cloud storage directly

See `CLAUDE.md` for detailed security architecture documentation.

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [MCP](https://modelcontextprotocol.io/) (Model Context Protocol)
- Search powered by [ugrep](https://github.com/Genivia/ugrep)
- PDF processing via [poppler-utils](https://poppler.freedesktop.org/)
