"""
MCP Transport Configuration and Connection Settings.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Defines transport options (stdio, SSE), bounded timeouts, and retry policies.
"""

import sys
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

MCP_DEFAULT_TIMEOUT_SECONDS = 30.0
MCP_MAX_RETRIES = 2
MCP_RETRY_BACKOFF_SECONDS = 0.5


class MCPTransportConfig(BaseModel):
    """Configuration for connecting to an MCP Server."""
    transport_type: str = Field(
        default="stdio",
        description="Transport type: 'stdio' or 'sse'.",
    )
    server_command: Optional[str] = Field(
        default=sys.executable,
        description="Command to spawn MCP server (for stdio).",
    )
    server_args: list[str] = Field(
        default_factory=lambda: ["-m", "enhancement.mcp.server"],
        description="Command arguments to spawn MCP server.",
    )
    server_url: Optional[str] = Field(
        default=None,
        description="URL for SSE transport (e.g. 'http://localhost:8000/sse').",
    )
    timeout_seconds: float = Field(
        default=MCP_DEFAULT_TIMEOUT_SECONDS,
        description="Execution timeout in seconds.",
    )
    max_retries: int = Field(
        default=MCP_MAX_RETRIES,
        description="Maximum retry attempts for transient transport failures.",
    )


DEFAULT_TRANSPORT_CONFIG = MCPTransportConfig()
