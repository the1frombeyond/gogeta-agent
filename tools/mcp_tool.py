#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Client Support

Backward-compatibility shim. The original 7830-line module has been split
into ``tools/mcp/`` package. This file re-exports all public and internal
names so existing importers continue to work without changes.

Configuration is read from ~/.gogeta/config.yaml under the ``mcp_servers`` key.
The ``mcp`` Python package is optional -- if not installed, this module is a
no-op (all operations return empty results).
"""

from __future__ import annotations

import sys as _sys
import types as _types

# ---------------------------------------------------------------------------
# Import every name from the package modules so that
# ``from tools.mcp_tool import X`` resolves directly.
# ---------------------------------------------------------------------------

from tools.mcp._state import (
    _MCP_AVAILABLE,
    _MCP_HTTP_AVAILABLE,
    _MCP_NEW_HTTP,
    _MCP_SAMPLING_TYPES,
    _MCP_NOTIFICATION_TYPES,
    _MCP_MESSAGE_HANDLER_SUPPORTED,
    _MCP_INJECTION_PATTERNS,
    _servers,
    _lock,
    _server_error_counts,
    _server_breaker_opened_at,
    _parallel_safe_servers,
    _mcp_tool_server_names,
    _mcp_loop,
    _mcp_thread,
    _stdio_pids,
    _orphan_stdio_pids,
    _stdio_pgids,
    _DEFAULT_TOOL_TIMEOUT,
    _DEFAULT_CONNECT_TIMEOUT,
    _MAX_RECONNECT_RETRIES,
    _MAX_INITIAL_CONNECT_RETRIES,
    _MAX_BACKOFF_SECONDS,
    _SAFE_ENV_KEYS,
    _CREDENTIAL_PATTERN,
    _ENV_VAR_PATTERN,
    _AUTH_ERROR_TYPES,
    _SESSION_EXPIRED_MARKERS,
    _CIRCUIT_BREAKER_THRESHOLD,
    _CIRCUIT_BREAKER_COOLDOWN_SEC,
    _UTILITY_CAPABILITY_METHODS,
    _UTILITY_CAPABILITY_ATTRS,
    _get_server_by_name,
    _sanitize_error,
    _exc_str,
    _safe_numeric,
    LATEST_PROTOCOL_VERSION,
)

from tools.mcp._server import MCPServerTask

from tools.mcp._sampling import SamplingHandler

from tools.mcp._loop import (
    _ensure_mcp_loop,
    _run_on_mcp_loop,
    _stop_mcp_loop,
    _kill_orphaned_mcp_children,
    _snapshot_child_pids,
    _mcp_loop_exception_handler,
    _interrupted_call_result,
)

from tools.mcp._transport import (
    InvalidMcpUrlError,
    NonMcpEndpointError,
    _build_safe_env,
    _validate_remote_mcp_url,
    _resolve_client_cert,
    _resolve_stdio_command,
    _prepend_path,
    _format_connect_error,
    _get_mcp_stderr_log,
    _write_stderr_log_header,
    _mcp_image_extension_for_mime_type,
    _cache_mcp_image_block,
    _check_message_handler_support,
)

from tools.mcp._config import (
    _load_mcp_config,
    _interpolate_env_vars,
)

from tools.mcp._auth import (
    _is_auth_error,
    _get_http_headers,
    _load_oauth_config,
    _load_authorization_header,
    _handle_auth_error_and_retry,
    _handle_session_expired_and_retry,
)

from tools.mcp._schema import (
    sanitize_mcp_name_component,
    _normalize_mcp_input_schema,
    _convert_mcp_schema,
    _convert_mcp_tool_to_gogeta_schema,
    _convert_gogeta_schema_to_mcp_tool,
    _mcp_tool_schema_to_dict,
    _tool_collection_to_list,
    _convert_mcp_prompt_to_gogeta,
    _convert_mcp_resource_to_gogeta,
    _make_tool_result,
    _normalize_name_filter,
    _parse_boolish,
    _build_utility_schemas,
    _check_mcp_tool_injection,
)

from tools.mcp._registration import (
    register_mcp_servers,
    _register_server_tools,
    _forget_mcp_tool_server,
    _track_mcp_tool_server,
    _existing_tool_names,
    _get_connected_server_info,
    _get_server_for_tool,
    _discover_one,
    _connect_server,
    _discover_and_register_server,
    _make_check_fn,
    _make_tool_handler,
    _make_list_resources_handler,
    _make_read_resource_handler,
    _make_list_prompts_handler,
    _make_get_prompt_handler,
    _select_utility_schemas,
)

from tools.mcp._handlers import (
    _handle_mcp_tool_call,
    _call_server_tool,
    _increment_server_error,
    _bump_server_error,
    _reset_server_error,
    _is_circuit_breaker_open,
    _handle_list_resources,
    _handle_read_resource,
    _handle_list_prompts,
    _handle_get_prompt,
)

from tools.mcp._shutdown import (
    _disconnect_sync,
    _disconnect_all_sync,
    _disconnect_server_async,
    _disconnect_all_servers_async,
    _get_connected_server_names,
    _is_server_connected,
)

from tools.mcp._api import (
    discover_mcp_tools,
    is_mcp_tool_parallel_safe,
    get_mcp_status,
    probe_mcp_server_tools,
    shutdown_mcp_servers,
)

# Also re-export SDK types that callers may reference
try:
    from mcp.types import (
        CreateMessageResult, CreateMessageResultWithTools, ErrorData,
        SamplingCapability, SamplingToolsCapability, TextContent, ToolUseContent,
    )
except ImportError:
    pass

try:
    from mcp.types import (
        ServerNotification,
        ToolListChangedNotification,
        PromptListChangedNotification,
        ResourceListChangedNotification,
    )
except ImportError:
    pass

try:
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:
    pass

try:
    from mcp.client.streamable_http import streamable_http_client
except ImportError:
    pass

try:
    from mcp.client.sse import sse_client
except ImportError:
    pass

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    pass

from typing import Any, Dict, List, Optional

import asyncio

# ---------------------------------------------------------------------------
# Re-export the BROADCAST_TOOL_SCHEMAS sentinel
# ---------------------------------------------------------------------------
from tools.mcp import BROADCAST_TOOL_SCHEMAS

# ---------------------------------------------------------------------------
# __getattr__ fallback: if any name wasn't explicitly imported above, try
# looking it up from the package. This catches edge cases where an importer
# references a name that was only in the original mcp_tool.py indirectly.
# ---------------------------------------------------------------------------

_MCP_PACKAGE_MODULES = {
    "tools.mcp._state", "tools.mcp._server", "tools.mcp._sampling",
    "tools.mcp._loop", "tools.mcp._transport", "tools.mcp._config",
    "tools.mcp._auth", "tools.mcp._schema", "tools.mcp._registration",
    "tools.mcp._handlers", "tools.mcp._shutdown", "tools.mcp._api",
    "tools.mcp",
}


def __getattr__(name: str):
    """Fallback: look up any un-imported name from the package modules."""
    for _mod_name in _MCP_PACKAGE_MODULES:
        _mod = _sys.modules.get(_mod_name)
        if _mod is not None and hasattr(_mod, name):
            return getattr(_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Return all names from the package plus re-exported SDK names."""
    _names = set()
    for _mod_name in _MCP_PACKAGE_MODULES:
        _mod = _sys.modules.get(_mod_name)
        if _mod is not None:
            _names.update(
                n for n in dir(_mod) if not n.startswith("__")
            )
    _names.update(("Any", "Dict", "List", "Optional", "asyncio"))
    _names.update(("ClientSession", "StdioServerParameters", "stdio_client"))
    _names.update(("streamablehttp_client", "streamable_http_client", "sse_client"))
    _names.update((
        "CreateMessageResult", "CreateMessageResultWithTools", "ErrorData",
        "SamplingCapability", "SamplingToolsCapability", "TextContent",
        "ToolUseContent",
    ))
    _names.update((
        "ServerNotification", "ToolListChangedNotification",
        "PromptListChangedNotification", "ResourceListChangedNotification",
    ))
    _names.update(("BROADCAST_TOOL_SCHEMAS",))
    return sorted(_names)
