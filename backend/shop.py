"""One way for the backend to reach the shop: the MCP server.

The HTTP routes need shop facts too -- the ticket board, the cash balance --
and the rule from Problem 5 still holds: there is no second shop-data layer.
So the backend speaks to the same `campus-customs` server, launched from the
same committed `.mcp.json`, that the agents use. Nothing here opens SQLite.

A thin wrapper rather than a pydantic-ai toolset, because an HTTP route needs
a tool result directly and has no agent to ask for it. Same server, same
config, same database -- just without a model in the middle.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic_ai.mcp import load_mcp_toolsets

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_CONFIG = REPO_ROOT / ".mcp.json"

_toolsets: list[Any] | None = None


def toolsets() -> list[Any]:
    """The MCP toolsets, loaded once and reused."""
    global _toolsets
    if _toolsets is None:
        _toolsets = load_mcp_toolsets(MCP_CONFIG)
    return _toolsets


def client():
    """The raw MCP client underneath the prefixed toolset."""
    first = toolsets()[0]
    return getattr(first, "wrapped", first).client


def _unwrap(result: Any) -> Any:
    """Pull the payload out of an MCP tool result.

    The SDK hands back structured content when the tool declares a schema and
    falls back to text blocks when it does not, so both are handled rather
    than assuming whichever one happened to come back during development.
    """
    payload = getattr(result, "structured_content", None)
    if payload is None:
        payload = getattr(result, "data", None)
    if payload is None:
        blocks = getattr(result, "content", result)
        text = blocks[0].text if isinstance(blocks, list) and blocks else blocks
        payload = json.loads(text) if isinstance(text, str) else text
    return payload


async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Call one tool on the campus-customs server and return its payload.

    Raises whatever the tool raised -- a refusal is a real answer and the route
    above turns it into an HTTP error the dashboard can show, rather than
    swallowing it into a success.
    """
    async with client() as session:
        return _unwrap(await session.call_tool(name, arguments or {}))
