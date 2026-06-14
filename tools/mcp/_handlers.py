import asyncio
import json
import logging
from typing import Any, Optional

from tools.mcp._state import (
    _MCP_AVAILABLE, _server_error_counts, _server_breaker_opened_at,
    _CIRCUIT_BREAKER_THRESHOLD, _CIRCUIT_BREAKER_COOLDOWN_SEC,
    _parallel_safe_servers, _get_server_by_name, _lock,
    logger,
)
from tools.mcp._transport import _sanitize_error, _exc_str
from tools.mcp._loop import _run_on_mcp_loop
from tools.mcp._schema import _make_tool_result

logger = logging.getLogger(__name__)


def _call_server_tool(
    server_name: str,
    tool_name: str,
    arguments: dict,
    timeout: float = 120,
) -> str:
    """Call a tool on an MCP server and return the result as JSON."""
    from tools.interrupt import is_interrupted

    if is_interrupted():
        return _interrupted_call_result()

    if not _MCP_AVAILABLE:
        return _make_tool_result("MCP SDK not available", is_error=True)

    server = _get_server_by_name(server_name)
    if server is None:
        return _make_tool_result(
            f"MCP server '{server_name}' is not connected", is_error=True,
        )
    if server.session is None:
        return _make_tool_result(
            f"MCP server '{server_name}' session is not initialized", is_error=True,
        )

    safe_server = server_name
    if safe_server in _parallel_safe_servers:
        rpc_lock = None
    else:
        rpc_lock = server._rpc_lock

    async def _do_call():
        try:
            if rpc_lock is not None:
                async with rpc_lock:
                    result = await server.session.call_tool(tool_name, arguments)
            else:
                result = await server.session.call_tool(tool_name, arguments)

            content = result.content if hasattr(result, "content") else []
            is_error = getattr(result, "isError", False)
            serialized = []
            for block in content:
                if hasattr(block, "text"):
                    serialized.append({"type": "text", "text": block.text})
                elif hasattr(block, "data"):
                    from tools.mcp._transport import _cache_mcp_image_block
                    cached = _cache_mcp_image_block(block)
                    if cached:
                        serialized.append({"type": "image", "source": cached})
                    else:
                        serialized.append({"type": "data", "data": str(block.data)[:500]})
                else:
                    serialized.append({"type": "unknown", "data": str(block)[:500]})
            return _make_tool_result(serialized, is_error)
        except Exception as exc:
            return _make_tool_result(
                f"MCP tool call error: {_sanitize_error(_exc_str(exc))}", is_error=True,
            )

    try:
        result_data = _run_on_mcp_loop(_do_call(), timeout=timeout)
        if isinstance(result_data, dict):
            return json.dumps(result_data, ensure_ascii=False)
        return str(result_data)
    except TimeoutError as exc:
        _increment_server_error(server_name)
        return _make_tool_result(str(exc), is_error=True)
    except Exception as exc:
        _increment_server_error(server_name)
        return _make_tool_result(
            f"MCP tool call failed: {_sanitize_error(_exc_str(exc))}", is_error=True,
        )


def _handle_mcp_tool_call(
    safe_server: str,
    safe_tool: str,
    args: dict,
    timeout: float,
    task_id: str = None,
) -> str:
    return _call_server_tool(safe_server, safe_tool, args, timeout)


def _handle_list_resources(
    safe_server: str, timeout: float, task_id: str = None,
) -> str:
    server = _get_server_by_name(safe_server)
    if server is None or server.session is None:
        return _make_tool_result(f"MCP server '{safe_server}' not connected", is_error=True)

    async def _do():
        try:
            result = await server.session.list_resources()
            resources = result.resources if hasattr(result, "resources") else []
            serialized = [
                {"uri": r.uri, "name": getattr(r, "name", ""), "description": getattr(r, "description", "")}
                for r in resources
            ]
            return _make_tool_result(json.dumps(serialized, ensure_ascii=False))
        except Exception as exc:
            return _make_tool_result(f"list_resources failed: {_exc_str(exc)}", is_error=True)

    return json.dumps(_run_on_mcp_loop(_do(), timeout=timeout), ensure_ascii=False)


def _handle_read_resource(
    safe_server: str, uri: str, timeout: float, task_id: str = None,
) -> str:
    server = _get_server_by_name(safe_server)
    if server is None or server.session is None:
        return _make_tool_result(f"MCP server '{safe_server}' not connected", is_error=True)

    async def _do():
        try:
            result = await server.session.read_resource(uri)
            contents = result.contents if hasattr(result, "contents") else []
            serialized = []
            for c in contents:
                text = getattr(c, "text", None)
                blob = getattr(c, "blob", None)
                if text is not None:
                    serialized.append({"type": "text", "text": text})
                elif blob is not None:
                    serialized.append({"type": "blob", "mimeType": getattr(c, "mimeType", ""), "data": str(blob)[:500]})
            return _make_tool_result(serialized)
        except Exception as exc:
            return _make_tool_result(f"read_resource failed: {_exc_str(exc)}", is_error=True)

    return json.dumps(_run_on_mcp_loop(_do(), timeout=timeout), ensure_ascii=False)


def _handle_list_prompts(
    safe_server: str, timeout: float, task_id: str = None,
) -> str:
    server = _get_server_by_name(safe_server)
    if server is None or server.session is None:
        return _make_tool_result(f"MCP server '{safe_server}' not connected", is_error=True)

    async def _do():
        try:
            result = await server.session.list_prompts()
            prompts = result.prompts if hasattr(result, "prompts") else []
            serialized = [{"name": p.name, "description": getattr(p, "description", "")} for p in prompts]
            return _make_tool_result(json.dumps(serialized, ensure_ascii=False))
        except Exception as exc:
            return _make_tool_result(f"list_prompts failed: {_exc_str(exc)}", is_error=True)

    return json.dumps(_run_on_mcp_loop(_do(), timeout=timeout), ensure_ascii=False)


def _handle_get_prompt(
    safe_server: str, name: str, arguments: Optional[dict], timeout: float, task_id: str = None,
) -> str:
    server = _get_server_by_name(safe_server)
    if server is None or server.session is None:
        return _make_tool_result(f"MCP server '{safe_server}' not connected", is_error=True)

    async def _do():
        try:
            result = await server.session.get_prompt(name, arguments)
            messages = result.messages if hasattr(result, "messages") else []
            serialized = [{"role": m.role, "content": str(m.content)} for m in messages]
            return _make_tool_result(json.dumps(serialized, ensure_ascii=False))
        except Exception as exc:
            return _make_tool_result(f"get_prompt failed: {_exc_str(exc)}", is_error=True)

    return json.dumps(_run_on_mcp_loop(_do(), timeout=timeout), ensure_ascii=False)


def _interrupted_call_result() -> str:
    return json.dumps({
        "error": "MCP call interrupted: user sent a new message"
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


def _increment_server_error(server_name: str) -> None:
    import time
    now = time.monotonic()
    with _lock:
        count = _server_error_counts.get(server_name, 0)
        _server_error_counts[server_name] = count + 1
        if count + 1 >= _CIRCUIT_BREAKER_THRESHOLD:
            _server_breaker_opened_at[server_name] = now


def _bump_server_error(server_name: str) -> None:
    _increment_server_error(server_name)


def _reset_server_error(server_name: str) -> None:
    with _lock:
        _server_error_counts.pop(server_name, None)
        _server_breaker_opened_at.pop(server_name, None)


def _is_circuit_breaker_open(server_name: str) -> bool:
    import time
    with _lock:
        opened_at = _server_breaker_opened_at.get(server_name)
        if opened_at is None:
            return False
        if time.monotonic() - opened_at > _CIRCUIT_BREAKER_COOLDOWN_SEC:
            _server_breaker_opened_at.pop(server_name, None)
            _server_error_counts.pop(server_name, None)
            return False
        return True
