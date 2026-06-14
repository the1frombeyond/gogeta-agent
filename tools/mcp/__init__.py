# MCP tool package -- split from tools/mcp_tool.py
#
# This package provides MCP (Model Context Protocol) server management:
# connecting, discovering tools, tool call dispatch, and cleanup.

from tools.mcp._state import (
    _MCP_AVAILABLE,
    _MCP_HTTP_AVAILABLE,
    _MCP_SAMPLING_TYPES,
    _MCP_NOTIFICATION_TYPES,
    _MCP_MESSAGE_HANDLER_SUPPORTED,
    _MCP_INJECTION_PATTERNS,
    _servers,
    _lock,
    _parallel_safe_servers,
    _DEFAULT_TOOL_TIMEOUT,
    _DEFAULT_CONNECT_TIMEOUT,
    _get_server_by_name,
    _ENV_VAR_PATTERN,
)

from tools.mcp._loop import (
    _ensure_mcp_loop,
    _run_on_mcp_loop,
    _stop_mcp_loop,
    _kill_orphaned_mcp_children,
)

from tools.mcp._transport import (
    _build_safe_env,
    _sanitize_error,
    _exc_str,
    _validate_remote_mcp_url,
    _resolve_client_cert,
    InvalidMcpUrlError,
    NonMcpEndpointError,
)

from tools.mcp._sampling import SamplingHandler
from tools.mcp._server import MCPServerTask
from tools.mcp._schema import (
    sanitize_mcp_name_component,
    _normalize_mcp_input_schema,
    _convert_mcp_schema,
    _convert_mcp_tool_to_gogeta_schema,
    _make_tool_result,
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
)
from tools.mcp._shutdown import (
    _disconnect_sync,
    _disconnect_all_sync,
    _disconnect_server_async,
    _disconnect_all_servers_async,
    _get_connected_server_names,
    _is_server_connected,
)
from tools.mcp._handlers import (
    _handle_mcp_tool_call,
    _call_server_tool,
    _increment_server_error,
    _is_circuit_breaker_open,
    _bump_server_error,
    _reset_server_error,
)
from tools.mcp._auth import (
    _is_auth_error,
    _get_http_headers,
    _load_oauth_config,
    _load_authorization_header,
)
from tools.mcp._config import _load_mcp_config, _interpolate_env_vars

from tools.mcp._api import (
    discover_mcp_tools,
    is_mcp_tool_parallel_safe,
    get_mcp_status,
    probe_mcp_server_tools,
    shutdown_mcp_servers,
)

# BROADCAST_TOOL_SCHEMAS: exported for the MCP broadcast/SSE tool mechanism.
# This is a reference to the module-level _servers dict that allows
# external modules (e.g. tools/mcp_broadcast.py, gateway SSE endpoints)
# to enumerate active servers and their schema metadata.
BROADCAST_TOOL_SCHEMAS = _servers

__all__ = [
    "MCPServerTask",
    "SamplingHandler",
    "register_mcp_servers",
    "_register_server_tools",
    "_forget_mcp_tool_server",
    "_track_mcp_tool_server",
    "_disconnect_sync",
    "_disconnect_all_sync",
    "_disconnect_server_async",
    "_disconnect_all_servers_async",
    "_disconnect_one",
    "_get_connected_server_names",
    "_is_server_connected",
    "_ensure_mcp_loop",
    "_run_on_mcp_loop",
    "_stop_mcp_loop",
    "_build_safe_env",
    "_sanitize_error",
    "_exc_str",
    "_validate_remote_mcp_url",
    "_resolve_client_cert",
    "_handle_mcp_tool_call",
    "_call_server_tool",
    "_increment_server_error",
    "_bump_server_error",
    "_reset_server_error",
    "_is_circuit_breaker_open",
    "_handle_auth_error_and_retry",
    "_handle_session_expired_and_retry",
    "_is_auth_error",
    "_get_http_headers",
    "_load_oauth_config",
    "_load_authorization_header",
    "_load_mcp_config",
    "_interpolate_env_vars",
    "_normalize_mcp_input_schema",
    "_convert_mcp_schema",
    "_convert_mcp_tool_to_gogeta_schema",
    "_make_tool_result",
    "_existing_tool_names",
    "_get_connected_server_info",
    "_get_server_for_tool",
    "_get_server_by_name",
    "_discover_one",
    "_connect_server",
    "_discover_and_register_server",
    "discover_mcp_tools",
    "is_mcp_tool_parallel_safe",
    "get_mcp_status",
    "probe_mcp_server_tools",
    "shutdown_mcp_servers",
    "_kill_orphaned_mcp_children",
    "sanitize_mcp_name_component",
    "InvalidMcpUrlError",
    "NonMcpEndpointError",
    "_MCP_AVAILABLE",
    "_MCP_HTTP_AVAILABLE",
    "_MCP_SAMPLING_TYPES",
    "_MCP_NOTIFICATION_TYPES",
    "_MCP_MESSAGE_HANDLER_SUPPORTED",
    "_MCP_INJECTION_PATTERNS",
    "_ENV_VAR_PATTERN",
    "_servers",
    "_lock",
    "_parallel_safe_servers",
    "_DEFAULT_TOOL_TIMEOUT",
    "_DEFAULT_CONNECT_TIMEOUT",
    "BROADCAST_TOOL_SCHEMAS",
]
