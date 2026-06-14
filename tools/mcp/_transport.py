import json
import logging
import os
import re
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from tools.mcp._state import (
    logger,
    _MCP_AVAILABLE,
    _SAFE_ENV_KEYS,
    _CREDENTIAL_PATTERN,
    _lock,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stdio stderr redirection
# ---------------------------------------------------------------------------

_mcp_stderr_log_fh: Optional[Any] = None
_mcp_stderr_log_lock = threading.Lock()


def _get_mcp_stderr_log() -> Any:
    global _mcp_stderr_log_fh
    with _mcp_stderr_log_lock:
        if _mcp_stderr_log_fh is not None:
            return _mcp_stderr_log_fh
        try:
            from gogeta_constants import get_gogeta_home
            log_dir = get_gogeta_home() / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "mcp-stderr.log"
            fh = open(log_path, "a", encoding="utf-8", errors="replace", buffering=1)
            fh.fileno()
            _mcp_stderr_log_fh = fh
        except Exception as exc:
            logger.debug("Failed to open MCP stderr log, using devnull: %s", exc)
            try:
                _mcp_stderr_log_fh = open(os.devnull, "w", encoding="utf-8")
            except Exception:
                _mcp_stderr_log_fh = sys.stderr
        return _mcp_stderr_log_fh


def _write_stderr_log_header(server_name: str) -> None:
    fh = _get_mcp_stderr_log()
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fh.write(f"\n===== [{ts}] starting MCP server '{server_name}' =====\n")
        fh.flush()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# SDK availability checks
# ---------------------------------------------------------------------------

def _check_message_handler_support() -> bool:
    if not _MCP_AVAILABLE:
        return False
    try:
        import inspect
        from mcp import ClientSession
        return "message_handler" in inspect.signature(ClientSession).parameters
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

def _build_safe_env(user_env: Optional[dict]) -> dict:
    env = {}
    for key in _SAFE_ENV_KEYS:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value
    if user_env:
        env.update(user_env)
    return env


def _sanitize_error(text: str) -> str:
    return _CREDENTIAL_PATTERN.sub("<redacted>", text)


def _exc_str(exc: BaseException) -> str:
    msg = str(exc)
    if msg:
        return msg
    return type(exc).__name__


def _prepend_path(env: dict, directory: str) -> dict:
    if not directory:
        return env
    new_env = dict(env)
    current_path = new_env.get("PATH", "")
    if current_path:
        new_env["PATH"] = f"{directory}{os.pathsep}{current_path}"
    else:
        new_env["PATH"] = directory
    return new_env


# ---------------------------------------------------------------------------
# URL / transport helpers
# ---------------------------------------------------------------------------

def _resolve_stdio_command(command: str, env: dict) -> tuple[str, dict]:
    if os.path.isabs(command):
        return command, env
    resolved = None
    path_env = env.get("PATH", os.environ.get("PATH", ""))
    for directory in path_env.split(os.pathsep):
        candidate = os.path.join(directory, command)
        if os.path.isfile(candidate):
            resolved = os.path.abspath(candidate)
            break
    if resolved:
        return resolved, env
    if sys.platform == "win32":
        for ext in (".cmd", ".bat", ".exe", ".ps1"):
            cmd_ext = command + ext
            for directory in path_env.split(os.pathsep):
                candidate = os.path.join(directory, cmd_ext)
                if os.path.isfile(candidate):
                    return os.path.abspath(candidate), env
    return command, env


# ---------------------------------------------------------------------------
# Image caching
# ---------------------------------------------------------------------------

_MIME_EXT_MAP = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def _mcp_image_extension_for_mime_type(mime_type: str) -> str:
    return _MIME_EXT_MAP.get(mime_type, ".bin")


def _cache_mcp_image_block(block) -> str:
    try:
        mime_type = getattr(block, "mimeType", None) or getattr(block, "mime_type", None) or ""
        data = getattr(block, "data", None)
        if not data:
            return ""
        import base64
        raw = base64.b64decode(data) if isinstance(data, str) else data
        ext = _mcp_image_extension_for_mime_type(mime_type)
        from tools.image_cache import cache_image_from_bytes
        return cache_image_from_bytes(raw, ext)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class InvalidMcpUrlError(ValueError):
    pass


class NonMcpEndpointError(ConnectionError):
    pass


def _validate_remote_mcp_url(server_name: str, url: Any) -> str:
    if not url or not isinstance(url, str):
        raise InvalidMcpUrlError(
            f"MCP server '{server_name}': 'url' must be a non-empty string"
        )
    parsed = urlparse(url)
    if not parsed.scheme:
        raise InvalidMcpUrlError(
            f"MCP server '{server_name}': URL '{url}' is missing a scheme "
            f"(e.g. 'https://'). Add the scheme or use the 'command' key "
            f"for stdio transport."
        )
    if parsed.scheme not in ("http", "https"):
        raise InvalidMcpUrlError(
            f"MCP server '{server_name}': URL '{url}' has unsupported scheme "
            f"'{parsed.scheme}'. Only 'http' and 'https' are supported."
        )
    return url


def _resolve_client_cert(server_name: str, config: dict):
    cert = config.get("client_certificate")
    if cert and isinstance(cert, str):
        path = os.path.expanduser(cert)
        if os.path.isfile(path):
            return path
        logger.warning(
            "MCP server '%s': client_cert '%s' not found, skipping",
            server_name, cert,
        )
    return None


def _format_connect_error(exc: BaseException) -> str:
    from tools.mcp._state import _MCP_HTTP_AVAILABLE
    msg = str(exc) or type(exc).__name__
    sanitized = _sanitize_error(msg)
    if isinstance(exc, InvalidMcpUrlError):
        return str(exc)
    if isinstance(exc, NonMcpEndpointError):
        return str(exc)
    if isinstance(exc, ImportError):
        return f"MCP HTTP transport not available: {sanitized}"
    if "Errno 111" in msg or "Errno 61" in msg or "Connection refused" in msg:
        return f"Cannot connect to MCP server (connection refused): {sanitized}"
    return sanitized


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
