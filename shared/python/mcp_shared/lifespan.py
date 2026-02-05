"""
MCP server lifespan management utilities.

Provides factory functions for creating async context managers
that handle server startup and shutdown.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Dict

from mcp.server.fastmcp import FastMCP


def create_lifespan(
    get_connection: Callable,
    cleanup_connection: Callable,
    server_name: str,
    logger: logging.Logger
):
    """
    Factory to create an MCP server lifespan context manager.

    The lifespan handles:
    - Attempting connection on startup (with warning if unavailable)
    - Cleaning up connection on shutdown
    - Logging startup/shutdown events

    Args:
        get_connection: Function to get/create the plugin connection
        cleanup_connection: Function to cleanup the connection
        server_name: Name of the server for logging
        logger: Logger instance to use

    Returns:
        Async context manager suitable for FastMCP lifespan parameter

    Example:
        ```python
        from mcp_shared import create_lifespan, create_connection_manager

        get_conn, cleanup = create_connection_manager(...)
        lifespan = create_lifespan(get_conn, cleanup, "RhinoMCP", logger)

        mcp = FastMCP("RhinoMCP", lifespan=lifespan)
        ```
    """
    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
        try:
            logger.info(f"{server_name} server starting up")

            # Try to connect on startup to verify availability
            try:
                get_connection()
                logger.info(f"Successfully connected to {server_name} plugin on startup")
            except Exception as e:
                logger.warning(f"Could not connect to {server_name} plugin on startup: {str(e)}")
                logger.warning("Make sure the plugin is running before using tools")

            # Return empty context - connection is managed globally
            yield {}

        finally:
            logger.info(f"Shutting down {server_name} server")
            cleanup_connection()
            logger.info(f"{server_name} server shut down")

    return lifespan


def create_simple_lifespan(server_name: str, logger: logging.Logger):
    """
    Create a minimal lifespan that just logs startup/shutdown.

    Use this when the server doesn't need connection management
    (e.g., for documentation-only servers).

    Args:
        server_name: Name of the server for logging
        logger: Logger instance to use

    Returns:
        Async context manager suitable for FastMCP lifespan parameter
    """
    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
        logger.info(f"{server_name} server starting up")
        try:
            yield {}
        finally:
            logger.info(f"{server_name} server shut down")

    return lifespan
