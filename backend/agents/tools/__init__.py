import os
import json
import urllib
from urllib.parse import urlparse
from langchain_mcp_adapters.client import (
    MultiServerMCPClient,
    SSEConnection,
    StreamableHttpConnection,
    StdioConnection,
)


def _build_connection(host: str, transport: str, port: str = None, auth_headers=None):
    if auth_headers is None:
        auth_headers = {}
    if port:
        port = f":{port}"
    else:
        port = ""
    url = f"{host}{port}/{transport}"
    if transport == "sse":
        return SSEConnection(url=url, transport="sse", headers=auth_headers)
    elif transport == "stdio":
        return StdioConnection(transport="stdio")
    return StreamableHttpConnection(
        url=url, transport="streamable_http", headers=auth_headers
    )


# MULTIPLE MCP SERVERS
mcp_client = MultiServerMCPClient(
    {
        "underwriting_guidelines": _build_connection(
            host=os.getenv("MCP_HOST1"),
            port=os.getenv("MCP_PORT1"),
            transport=os.getenv("MCP_TRANSPORT1"),
            auth_headers=None,
        ),
        "crm_tools": _build_connection(
            host=os.getenv("MCP_HOST2"),
            port=os.getenv("MCP_PORT2"),
            transport=os.getenv("MCP_TRANSPORT2"),
            auth_headers=None,
        ),
        "medical_tools": _build_connection(
            host=os.getenv("MCP_HOST3"),
            port=os.getenv("MCP_PORT3"),
            transport=os.getenv("MCP_TRANSPORT3"),
            auth_headers=None,
        ),
    }
)


def _get_user_token(base_url: str, username: str, password: str) -> str:
    """Authenticate with username/password and return the access token."""
    parsed = urlparse(base_url)
    api_base = f"{parsed.scheme}://{parsed.netloc}"
    payload = json.dumps({"email": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{api_base}/auth/login",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
    return body["access_token"]


def _build_context_forge_client(
    token: str = None, mcp_host: str = None
) -> MultiServerMCPClient:
    """Build a MultiServerMCPClient targeting the Context Forge virtual MCP server.

    Args:
        token: Bearer token used to authenticate against Context Forge. When provided,
               it is sent as an ``Authorization: Bearer <token>`` header on every request.
               Pass ``None`` (or omit) to connect without authentication.
        mcp_host: Base URL of the Context Forge MCP host
                  (e.g. ``http://mcp-context-forge:4444``).  The transport path is
                  appended automatically from the ``CONTEXT_FORGE_MCP_TRANSPORT``
                  environment variable.  Defaults to ``None``, in which case the
                  connection URL will be incomplete — always supply this value in
                  production.

    Returns:
        A :class:`MultiServerMCPClient` instance with a single server entry keyed
        ``"context_forge"``, ready to call :py:meth:`get_tools`.
    """
    auth_headers = {"Authorization": f"Bearer {token}"} if token else {}
    return MultiServerMCPClient(
        {
            "context_forge": _build_connection(
                host=mcp_host,
                port=None,
                transport=os.getenv("CONTEXT_FORGE_MCP_TRANSPORT"),
                auth_headers=auth_headers,
            )
        }
    )


_cached_mcp_tools = None


async def get_mcp_tools():
    """Fetch MCP tools once and cache for subsequent calls."""
    global _cached_mcp_tools
    if _cached_mcp_tools is None:
        _cached_mcp_tools = await mcp_client.get_tools()
    return _cached_mcp_tools


async def get_mcp_tools_context_forge(token: str = None, mcp_host: str = None):
    """Fetch MCP tools from the Context Forge virtual MCP server.

    A fresh client is built on every call because ``token`` and ``mcp_host``
    differ between requests (e.g. broker vs analyst persona).

    The caller is responsible for building the full server URL following the
    Context Forge convention::

        <CONTEXT_FORGE_BASE_URL>/servers/<virtual_server_id>

    Example::

        base = os.getenv("CONTEXT_FORGE_BASE_URL")          # e.g. http://mcp-context-forge:4444
        mcp_host = f"{base}/servers/{virtual_server_id}"    # e.g. .../servers/broker
        tools = await get_mcp_tools_context_forge(token=token, mcp_host=mcp_host)

    Args:
        token: Bearer token used to authenticate against Context Forge.
               Injected as an ``Authorization: Bearer <token>`` header.
               Pass ``None`` to connect without authentication.
        mcp_host: Full URL of the target virtual MCP server, i.e.
                  ``<CONTEXT_FORGE_BASE_URL>/servers/<virtual_server_id>``.
                  The transport path (``sse`` / ``streamable_http``) is appended
                  automatically from the ``CONTEXT_FORGE_MCP_TRANSPORT`` env var.

    Returns:
        List of LangChain tools retrieved from the Context Forge virtual MCP server.
    """
    return await _build_context_forge_client(token=token, mcp_host=mcp_host).get_tools()
