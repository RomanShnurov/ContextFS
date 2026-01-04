"""Fathom MCP - File-first knowledge base MCP server."""

try:
    from importlib.metadata import version

    __version__ = version("fathom-mcp")
except Exception:
    __version__ = "0.1.0"

__all__ = ["__version__"]
