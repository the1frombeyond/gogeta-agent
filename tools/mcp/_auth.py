import asyncio
import json
import logging
import os
import time
from typing import Optional

from tools.mcp._state import (
    _AUTH_ERROR_TYPES, _SESSION_EXPIRED_MARKERS,
    _servers, _lock, _mcp_loop, _server_error_counts,
    logger,
)

logger = logging.getLogger(__name__)


def _get_auth_error_types():
    """Lazy-load auth error types from httpx or requests."""
    global _AUTH_ERROR_TYPES
    if _AUTH_ERROR_TYPES:
        return _AUTH_ERROR_TYPES
    try:
        import httpx
        _AUTH_ERROR_TYPES = (httpx.HTTPStatusError,)
    except ImportError:
        _AUTH_ERROR_TYPES = ()
    return _AUTH_ERROR_TYPES


def _is_session_expired_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(marker in msg for marker in _SESSION_EXPIRED_MARKERS)


def _should_reconnect_on_error(exc: BaseException, attempt: int) -> bool:
    if _is_session_expired_error(exc):
        return True
    auth_types = _get_auth_error_types()
    if auth_types and isinstance(exc, auth_types):
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    return False


def _load_oauth_config(server_name: str, config: dict) -> Optional[dict]:
    oauth = config.get("oauth")
    if not oauth or not isinstance(oauth, dict):
        return None

    client_id = oauth.get("client_id") or config.get("oauth_client_id")
    client_secret = oauth.get("client_secret") or config.get("oauth_client_secret")
    token_url = oauth.get("token_url") or config.get("oauth_token_url")
    scopes = oauth.get("scopes", [])

    if client_id and token_url:
        return {
            "client_id": client_id,
            "client_secret": client_secret or "",
            "token_url": token_url,
            "scopes": scopes,
        }

    return None


def _load_authorization_header(server_name: str, config: dict) -> Optional[str]:
    auth_value = config.get("authorization") or config.get("auth") or config.get("api_key")
    if auth_value:
        return auth_value

    env_var = config.get("auth_env_var") or config.get("api_key_env")
    if env_var:
        value = os.environ.get(env_var)
        if value:
            return value

    return None


def _is_auth_error(exc: BaseException) -> bool:
    types = _get_auth_error_types()
    if not types or not isinstance(exc, types):
        return False
    try:
        import httpx
        if isinstance(exc, httpx.HTTPStatusError):
            return getattr(exc.response, "status_code", None) == 401
    except ImportError:
        pass
    return True


def _get_http_headers(server_name: str, config: dict) -> dict:
    headers = dict(config.get("headers", {}))
    auth_header = _load_authorization_header(server_name, config)
    if auth_header:
        if auth_header.startswith("Bearer ") or " " in auth_header:
            headers.setdefault("Authorization", auth_header)
        else:
            headers.setdefault("Authorization", f"Bearer {auth_header}")
    return headers


def _handle_auth_error_and_retry(
    server_name: str,
    exc: BaseException,
    retry_call,
    op_description: str,
):
    """Attempt auth recovery and one retry; return None to fall through."""
    if not _is_auth_error(exc):
        return None

    from tools.mcp._loop import _run_on_mcp_loop
    from tools.mcp._handlers import _increment_server_error

    from tools.mcp_oauth_manager import get_manager
    manager = get_manager()

    async def _recover():
        return await manager.handle_401(server_name, None)

    try:
        recovered = _run_on_mcp_loop(_recover(), timeout=10)
    except Exception as rec_exc:
        logger.warning("MCP OAuth '%s': recovery attempt failed: %s", server_name, rec_exc)
        recovered = False

    if recovered:
        with _lock:
            srv = _servers.get(server_name)
        if srv is not None and hasattr(srv, "_reconnect_event"):
            loop = _mcp_loop
            if loop is not None and loop.is_running():
                loop.call_soon_threadsafe(srv._reconnect_event.set)

                async def _await_ready() -> bool:
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        if srv.session is not None and srv._ready.is_set():
                            return True
                        await asyncio.sleep(0.25)
                    return False

                try:
                    _run_on_mcp_loop(_await_ready(), timeout=15)
                except Exception as exc:
                    logger.warning("MCP OAuth '%s': ready poll failed: %s", server_name, exc)

        _server_error_counts[server_name] = 0

        try:
            result = retry_call()
            try:
                parsed = json.loads(result)
                if "error" not in parsed:
                    _server_error_counts[server_name] = 0
                    return result
            except (json.JSONDecodeError, TypeError):
                _server_error_counts[server_name] = 0
                return result
        except Exception as retry_exc:
            logger.warning("MCP %s/%s retry after auth recovery failed: %s", server_name, op_description, retry_exc)

    _increment_server_error(server_name)
    return json.dumps({
        "error": (
            f"MCP server '{server_name}' requires re-authentication. "
            f"Run `gogeta mcp login {server_name}` (or delete the tokens "
            f"file under ~/.gogeta/mcp-tokens/ and restart). Do NOT retry "
            f"this tool — ask the user to re-authenticate."
        ),
        "needs_reauth": True,
        "server": server_name,
    }, ensure_ascii=False)


def _handle_session_expired_and_retry(
    server_name: str,
    exc: BaseException,
    retry_call,
    op_description: str,
):
    """Trigger a transport reconnect and retry once on session expiry."""
    if not _is_session_expired_error(exc):
        return None

    with _lock:
        srv = _servers.get(server_name)
    if srv is None or not hasattr(srv, "_reconnect_event"):
        return None

    loop = _mcp_loop
    if loop is None or not loop.is_running():
        return None

    logger.info(
        "MCP server '%s': %s failed with session-expired error (%s); "
        "signalling transport reconnect and retrying once.",
        server_name, op_description, exc,
    )

    loop.call_soon_threadsafe(srv._reconnect_event.set)
    deadline = time.monotonic() + 15
    ready = False
    while time.monotonic() < deadline:
        if srv.session is not None and srv._ready.is_set():
            ready = True
            break
        time.sleep(0.25)
    if not ready:
        logger.warning(
            "MCP server '%s': reconnect did not ready within 15s after "
            "session-expired error; falling through to error response.",
            server_name,
        )
        return None

    try:
        result = retry_call()
        try:
            parsed = json.loads(result)
            if "error" not in parsed:
                _server_error_counts[server_name] = 0
                return result
        except (json.JSONDecodeError, TypeError):
            _server_error_counts[server_name] = 0
            return result
    except Exception as retry_exc:
        logger.warning("MCP %s/%s retry after session reconnect failed: %s", server_name, op_description, retry_exc)
    return None
