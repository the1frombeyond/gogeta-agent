import logging
import re
import threading
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP SDK availability flags
# ---------------------------------------------------------------------------

_MCP_AVAILABLE = False
_MCP_HTTP_AVAILABLE = False
_MCP_SAMPLING_TYPES = False
_MCP_NOTIFICATION_TYPES = False
_MCP_MESSAGE_HANDLER_SUPPORTED = False
_MCP_NEW_HTTP = False
LATEST_PROTOCOL_VERSION = "2025-03-26"

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    _MCP_AVAILABLE = True

    try:
        from mcp.client.streamable_http import streamablehttp_client
        _MCP_HTTP_AVAILABLE = True
    except ImportError:
        _MCP_HTTP_AVAILABLE = False

    try:
        from mcp.client.streamable_http import streamable_http_client
        _MCP_NEW_HTTP = True
    except ImportError:
        _MCP_NEW_HTTP = False

    try:
        from mcp.types import LATEST_PROTOCOL_VERSION
    except ImportError:
        pass

    try:
        from mcp.client.sse import sse_client
    except ImportError:
        sse_client = None

    try:
        from mcp.types import (
            CreateMessageResult,
            CreateMessageResultWithTools,
            ErrorData,
            SamplingCapability,
            SamplingToolsCapability,
            TextContent,
            ToolUseContent,
        )
        _MCP_SAMPLING_TYPES = True
    except ImportError:
        pass

    try:
        from mcp.types import (
            ServerNotification,
            ToolListChangedNotification,
            PromptListChangedNotification,
            ResourceListChangedNotification,
        )
        _MCP_NOTIFICATION_TYPES = True
    except ImportError:
        pass
except ImportError:
    logger.debug("mcp package not installed -- MCP tool support disabled")
    sse_client = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TOOL_TIMEOUT = 120
_DEFAULT_CONNECT_TIMEOUT = 60
_MAX_RECONNECT_RETRIES = 5
_MAX_INITIAL_CONNECT_RETRIES = 3
_MAX_BACKOFF_SECONDS = 60

_SAFE_ENV_KEYS = frozenset({
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM", "SHELL", "TMPDIR",
})

_CREDENTIAL_PATTERN = re.compile(
    r"(?:"
    r"ghp_[A-Za-z0-9_]{1,255}"
    r"|sk-[A-Za-z0-9_]{1,255}"
    r"|Bearer\s+\S+"
    r"|token=[^\s&,;\"']{1,255}"
    r"|key=[^\s&,;\"']{1,255}"
    r"|API_KEY=[^\s&,;\"']{1,255}"
    r"|password=[^\s&,;\"']{1,255}"
    r"|secret=[^\s&,;\"']{1,255}"
    r")",
    re.IGNORECASE,
)

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

# ---------------------------------------------------------------------------
# Server state
# ---------------------------------------------------------------------------

_servers: Dict[str, Any] = {}

_server_error_counts: Dict[str, int] = {}
_server_breaker_opened_at: Dict[str, float] = {}
_CIRCUIT_BREAKER_THRESHOLD = 3
_CIRCUIT_BREAKER_COOLDOWN_SEC = 60.0

_parallel_safe_servers: set = set()
_mcp_tool_server_names: Dict[str, str] = {}

_mcp_loop: Optional[Any] = None
_mcp_thread: Optional[threading.Thread] = None
_lock = threading.Lock()

_stdio_pids: Dict[int, str] = {}
_orphan_stdio_pids: set = set()
_stdio_pgids: Dict[int, int] = {}

# ---------------------------------------------------------------------------
# Auth error types (lazy)
# ---------------------------------------------------------------------------

_AUTH_ERROR_TYPES: tuple = ()

# ---------------------------------------------------------------------------
# Session expired markers
# ---------------------------------------------------------------------------

_SESSION_EXPIRED_MARKERS: tuple = (
    "invalid or expired session",
    "expired session",
    "session expired",
    "session not found",
    "unknown session",
    "session terminated",
    "closedresourceerror",
    "closed resource",
    "transport is closed",
    "connection closed",
    "broken pipe",
    "end of file",
)

_MCP_INJECTION_PATTERNS: tuple = ()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _sanitize_error(text: str) -> str:
    return _CREDENTIAL_PATTERN.sub("<redacted>", text)


def _exc_str(exc: BaseException) -> str:
    msg = str(exc)
    if msg:
        return msg
    return type(exc).__name__


def _safe_numeric(value, default, coerce=int, minimum=1):
    if value is None:
        return default
    try:
        v = coerce(value)
        if v < minimum:
            return default
        return v
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Capability maps
# ---------------------------------------------------------------------------

_UTILITY_CAPABILITY_METHODS = {
    "list_resources": "list_resources",
    "read_resource": "read_resource",
    "list_prompts": "list_prompts",
    "get_prompt": "get_prompt",
}

_UTILITY_CAPABILITY_ATTRS = {
    "list_resources": "resources",
    "read_resource": "resources",
    "list_prompts": "prompts",
    "get_prompt": "prompts",
}


def _get_server_by_name(server_name: str):
    with _lock:
        return _servers.get(server_name)
