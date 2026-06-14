import asyncio
import logging
from typing import Dict, List, Optional

from tools.mcp._state import (
    _MCP_AVAILABLE, _servers, _lock, _mcp_tool_server_names,
    _parallel_safe_servers, _DEFAULT_TOOL_TIMEOUT, _DEFAULT_CONNECT_TIMEOUT,
)
from tools.mcp._config import _load_mcp_config
from tools.mcp._schema import _parse_boolish
from tools.mcp._schema import sanitize_mcp_name_component
from tools.mcp._loop import _ensure_mcp_loop, _run_on_mcp_loop, _stop_mcp_loop

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# High-level discovery
# ---------------------------------------------------------------------------


def discover_mcp_tools() -> List[str]:
    """Entry point: load config, connect to MCP servers, register tools.

    Called from model_tools after discover_builtin_tools(). Safe to call
    even when the mcp package is not installed (returns empty list).

    Idempotent for already-connected servers. If some servers failed on
    a previous call, only the missing ones are retried.

    Returns:
        List of all registered MCP tool names.
    """
    if not _MCP_AVAILABLE:
        logger.debug("MCP SDK not available -- skipping MCP tool discovery")
        return []

    servers = _load_mcp_config()
    if not servers:
        logger.debug("No MCP servers configured")
        return []

    with _lock:
        new_server_names = [
            name
            for name, cfg in servers.items()
            if name not in _servers and _parse_boolish(cfg.get("enabled", True), default=True)
        ]

    from tools.mcp._registration import register_mcp_servers
    tool_names = register_mcp_servers(servers)

    if not new_server_names:
        return tool_names

    with _lock:
        connected_server_names = [name for name in new_server_names if name in _servers]
        new_tool_count = sum(
            len(getattr(_servers[name], "_registered_tool_names", []))
            for name in connected_server_names
        )

    failed_count = len(new_server_names) - len(connected_server_names)
    if new_tool_count or failed_count:
        summary = f"  MCP: {new_tool_count} tool(s) from {len(connected_server_names)} server(s)"
        if failed_count:
            summary += f" ({failed_count} failed)"
        logger.info(summary)

    return tool_names


# ---------------------------------------------------------------------------
# Parallel-safety check
# ---------------------------------------------------------------------------


def is_mcp_tool_parallel_safe(tool_name: str) -> bool:
    """Check if an MCP tool belongs to a server that supports parallel tool calls.

    MCP tool names follow the pattern mcp_{server}_{tool}, but that string
    shape is ambiguous when server names contain underscores. Use the exact
    server provenance captured at registration time rather than prefix
    matching, then check whether that server's config includes
    supports_parallel_tool_calls: true.

    Returns False for non-MCP tools or tools from servers without the flag.
    """
    if not tool_name.startswith("mcp_"):
        return False
    with _lock:
        server_name = _mcp_tool_server_names.get(tool_name)
        return bool(server_name and server_name in _parallel_safe_servers)


# ---------------------------------------------------------------------------
# Server status (for banner / TUI display)
# ---------------------------------------------------------------------------


def get_mcp_status() -> List[dict]:
    """Return status of all configured MCP servers for banner display.

    Returns a list of dicts with keys: name, transport, tools, connected.
    Includes both successfully connected servers and configured-but-failed ones.
    """
    result: List[dict] = []

    configured = _load_mcp_config()
    if not configured:
        return result

    with _lock:
        active_servers = dict(_servers)

    for name, cfg in configured.items():
        transport = cfg.get("transport", "http") if "url" in cfg else "stdio"
        enabled = _parse_boolish(cfg.get("enabled", True), default=True)
        server = active_servers.get(name)
        if server and server.session is not None:
            entry = {
                "name": name,
                "transport": transport,
                "tools": len(server._registered_tool_names) if hasattr(server, "_registered_tool_names") else len(server._tools),
                "connected": True,
                "disabled": False,
            }
            if server._sampling:
                entry["sampling"] = dict(server._sampling.metrics)
            result.append(entry)
        else:
            result.append({
                "name": name,
                "transport": transport,
                "tools": 0,
                "connected": False,
                "disabled": not enabled,
            })

    return result


# ---------------------------------------------------------------------------
# Probe (temporary connect for interactive config)
# ---------------------------------------------------------------------------


def probe_mcp_server_tools() -> Dict[str, List[tuple]]:
    """Temporarily connect to configured MCP servers and list their tools.

    Designed for gogeta tools interactive configuration -- connects to each
    enabled server, grabs tool names and descriptions, then disconnects.
    Does NOT register tools in the Gogeta registry.

    Returns:
        Dict mapping server name to list of (tool_name, description) tuples.
        Servers that fail to connect are omitted from the result.
    """
    if not _MCP_AVAILABLE:
        return {}

    servers_config = _load_mcp_config()
    if not servers_config:
        return {}

    enabled = {
        k: v for k, v in servers_config.items()
        if _parse_boolish(v.get("enabled", True), default=True)
    }
    if not enabled:
        return {}

    _ensure_mcp_loop()

    result: Dict[str, List[tuple]] = {}
    probed_servers: list = []

    async def _probe_all():
        names = list(enabled.keys())
        coros = []
        for name, cfg in enabled.items():
            ct = cfg.get("connect_timeout", _DEFAULT_CONNECT_TIMEOUT)
            from tools.mcp._server import MCPServerTask
            srv = MCPServerTask(name)
            coros.append(asyncio.wait_for(srv.start(cfg), timeout=ct))
            probed_servers.append(srv)

        outcomes = await asyncio.gather(*coros, return_exceptions=True)

        for name, outcome in zip(names, outcomes):
            if isinstance(outcome, Exception):
                logger.debug("Probe: failed to connect to '%s': %s", name, outcome)
                continue
            tools = []
            for t in outcome._tools:
                desc = getattr(t, "description", "") or ""
                tools.append((t.name, desc))
            result[name] = tools

        await asyncio.gather(
            *(s.shutdown() for s in probed_servers),
            return_exceptions=True,
        )

    try:
        _run_on_mcp_loop(_probe_all(), timeout=120)
    except Exception as exc:
        logger.debug("MCP probe failed: %s", exc)
    finally:
        _stop_mcp_loop()

    return result


# ---------------------------------------------------------------------------
# Shutdown all servers
# ---------------------------------------------------------------------------


def shutdown_mcp_servers():
    """Close all MCP server connections and stop the background loop.

    Each server Task is signalled to exit its async with block so that
    the anyio cancel-scope cleanup happens in the same Task that opened it.
    All servers are shut down in parallel via asyncio.gather.
    """
    from tools.mcp._shutdown import _disconnect_all_sync

    with _lock:
        servers_snapshot = list(_servers.values())

    if not servers_snapshot:
        _stop_mcp_loop()
        return

    async def _shutdown():
        results = await asyncio.gather(
            *(server.shutdown() for server in servers_snapshot),
            return_exceptions=True,
        )
        for server, result in zip(servers_snapshot, results):
            if isinstance(result, Exception):
                logger.debug(
                    "Error closing MCP server '%s': %s", server.name, result,
                )
        with _lock:
            _servers.clear()

    with _lock:
        from tools.mcp._loop import _mcp_loop
        loop = _mcp_loop

    if loop is not None and loop.is_running():
        from agent.async_utils import safe_schedule_threadsafe
        future = safe_schedule_threadsafe(
            _shutdown(), loop,
            logger=logger,
            log_message="MCP shutdown: failed to schedule",
        )
        if future is not None:
            try:
                future.result(timeout=15)
            except BaseException as exc:
                logger.debug("Error during MCP shutdown: %s", exc)

    _stop_mcp_loop()
