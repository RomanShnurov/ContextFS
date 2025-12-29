"""MCP Resources for knowledge base."""

import json
import logging

from mcp.server import Server
from mcp.types import Resource, ResourceTemplate

from .config import Config
from .errors import McpError, collection_not_found, document_not_found
from .security import FileAccessControl

logger = logging.getLogger(__name__)


def register_resources(server: Server, config: Config) -> None:
    """Register MCP resources."""

    @server.list_resources()  # type: ignore
    async def list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="knowledge://index",  # type: ignore[arg-type]
                name="Knowledge Base Index",
                description="Root index of all collections",
                mimeType="application/json",
            ),
        ]

    @server.list_resource_templates()  # type: ignore
    async def list_resource_templates() -> list[ResourceTemplate]:
        """List resource URI templates."""
        return [
            ResourceTemplate(
                uriTemplate="knowledge://{path}/index",
                name="Collection Index",
                description="List of documents in a collection",
                mimeType="application/json",
            ),
            ResourceTemplate(
                uriTemplate="knowledge://{path}/info",
                name="Document Info",
                description="Document metadata and TOC",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()  # type: ignore
    async def read_resource(uri: str) -> str:
        """Read resource content."""
        logger.debug(f"Reading resource: {uri}")

        # Parse URI: knowledge://path/type
        if not uri.startswith("knowledge://"):
            logger.warning(f"Invalid URI scheme requested: {uri}")
            raise ValueError(f"Invalid URI scheme: {uri}")

        path_and_type = uri[len("knowledge://") :]

        try:
            if path_and_type == "index":
                return await _get_root_index(config)

            if path_and_type.endswith("/index"):
                path = path_and_type[:-6]  # Remove "/index"
                return await _get_collection_index(config, path)

            if path_and_type.endswith("/info"):
                path = path_and_type[:-5]  # Remove "/info"
                return await _get_document_info_resource(config, path)

            logger.warning(f"Unknown resource type requested: {uri}")
            raise ValueError(f"Unknown resource: {uri}")
        except McpError:
            # Re-raise MCP errors as-is
            raise
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise


async def _get_root_index(config: Config) -> str:
    """Get root index as JSON."""
    root = config.knowledge.root

    collections = []
    for item in sorted(root.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            collections.append(
                {
                    "name": item.name,
                    "path": item.name,
                    "type": "collection",
                }
            )

    return json.dumps(
        {
            "collections": collections,
            "root": str(root),
        },
        indent=2,
    )


async def _get_collection_index(config: Config, path: str) -> str:
    """Get collection index as JSON.

    Args:
        config: Server configuration
        path: Relative path to collection (validated for security)

    Returns:
        JSON string with collection contents

    Raises:
        McpError: If path is invalid, traversal detected, or collection not found
    """
    # Validate path using FileAccessControl to prevent path traversal
    access_control = FileAccessControl(config.knowledge.root, config)
    full_path = access_control.validate_path(path)

    if not full_path.exists():
        logger.warning(f"Collection not found: {path}")
        raise collection_not_found(path)

    if not full_path.is_dir():
        logger.warning(f"Path is not a collection (directory): {path}")
        raise collection_not_found(path)

    items = []
    for item in sorted(full_path.iterdir()):
        if item.name.startswith("."):
            continue

        if item.is_dir():
            items.append(
                {
                    "name": item.name,
                    "path": f"{path}/{item.name}",
                    "type": "collection",
                }
            )
        elif item.suffix.lower() in config.supported_extensions:
            items.append(
                {
                    "name": item.name,
                    "path": f"{path}/{item.name}",
                    "type": "document",
                    "format": item.suffix.lower().lstrip("."),
                }
            )

    return json.dumps({"items": items, "path": path}, indent=2)


async def _get_document_info_resource(config: Config, path: str) -> str:
    """Get document info as JSON.

    Args:
        config: Server configuration
        path: Relative path to document (validated for security)

    Returns:
        JSON string with document metadata

    Raises:
        McpError: If path is invalid, traversal detected, or document not found
    """
    from .tools.read import _get_document_info

    # Validate path using FileAccessControl to prevent path traversal
    access_control = FileAccessControl(config.knowledge.root, config)
    full_path = access_control.validate_path(path)

    if not full_path.exists():
        logger.warning(f"Document not found: {path}")
        raise document_not_found(path)

    if not full_path.is_file():
        logger.warning(f"Path is not a document (file): {path}")
        raise document_not_found(path)

    info = await _get_document_info(config, {"path": path})
    return json.dumps(info, indent=2)
