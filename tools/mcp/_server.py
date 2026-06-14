import asyncio
import json
import logging
import os
import signal
from typing import Any, Dict, List, Optional

from tools.mcp._state import (
    _MCP_AVAILABLE, _MCP_HTTP_AVAILABLE, _MCP_SAMPLING_TYPES,
    _MCP_NOTIFICATION_TYPES, _MCP_MESSAGE_HANDLER_SUPPORTED, _MCP_NEW_HTTP,
    _DEFAULT_TOOL_TIMEOUT, _DEFAULT_CONNECT_TIMEOUT,
    _MAX_RECONNECT_RETRIES, _MAX_INITIAL_CONNECT_RETRIES, _MAX_BACKOFF_SECONDS,
    _lock, _stdio_pids, _stdio_pgids, _orphan_stdio_pids,
    LATEST_PROTOCOL_VERSION,
    _get_server_by_name,
    logger,
)

# SDK imports -- guarded by _MCP_AVAILABLE at call sites
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None
    streamablehttp_client = None

try:
    from mcp.client.streamable_http import streamable_http_client
except ImportError:
    streamable_http_client = None

try:
    from mcp.client.sse import sse_client
except ImportError:
    sse_client = None

try:
    from mcp.types import (
        ServerNotification,
        ToolListChangedNotification,
        PromptListChangedNotification,
        ResourceListChangedNotification,
    )
except ImportError:
    ServerNotification = None
    ToolListChangedNotification = None
    PromptListChangedNotification = None
    ResourceListChangedNotification = None
from tools.mcp._transport import (
    _build_safe_env, _resolve_stdio_command, _write_stderr_log_header,
    _get_mcp_stderr_log, _validate_remote_mcp_url, _resolve_client_cert,
    _format_connect_error, _safe_numeric,
    InvalidMcpUrlError, NonMcpEndpointError,
)
from tools.mcp._loop import _snapshot_child_pids
from tools.mcp._sampling import SamplingHandler
from tools.mcp._auth import _is_auth_error

logger = logging.getLogger(__name__)


class MCPServerTask:
    __slots__ = (
        "name", "session", "tool_timeout",
        "_task", "_ready", "_shutdown_event", "_reconnect_event",
        "_tools", "_error", "_config",
        "_sampling", "_registered_tool_names", "_auth_type", "_refresh_lock",
        "_rpc_lock", "_pending_refresh_tasks",
        "initialize_result",
    )

    def __init__(self, name: str):
        self.name = name
        self.session: Optional[Any] = None
        self.tool_timeout: float = _DEFAULT_TOOL_TIMEOUT
        self._task: Optional[asyncio.Task] = None
        self._ready = asyncio.Event()
        self._shutdown_event = asyncio.Event()
        self._reconnect_event = asyncio.Event()
        self._tools: list = []
        self._error: Optional[Exception] = None
        self._config: dict = {}
        self._sampling: Optional[SamplingHandler] = None
        self._registered_tool_names: list[str] = []
        self._auth_type: str = ""
        self._refresh_lock = asyncio.Lock()
        self._rpc_lock = asyncio.Lock()
        self._pending_refresh_tasks: set[asyncio.Task] = set()
        self.initialize_result: Optional[Any] = None

    def _is_http(self) -> bool:
        return "url" in self._config

    # ----- Dynamic tool discovery -------------------------------------------

    async def _refresh_tools_task(self):
        try:
            await self._refresh_tools()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("MCP server '%s': dynamic tool refresh failed", self.name)

    def _schedule_tools_refresh(self) -> asyncio.Task:
        task = asyncio.create_task(self._refresh_tools_task())
        self._pending_refresh_tasks.add(task)
        task.add_done_callback(self._pending_refresh_tasks.discard)
        return task

    def _make_message_handler(self):
        async def _handler(message):
            try:
                if isinstance(message, Exception):
                    logger.debug("MCP message handler (%s): exception: %s", self.name, message)
                    return
                if _MCP_NOTIFICATION_TYPES and isinstance(message, ServerNotification):
                    match message.root:
                        case ToolListChangedNotification():
                            logger.info("MCP server '%s': received tools/list_changed notification", self.name)
                            self._schedule_tools_refresh()
                            await asyncio.sleep(0)
                        case PromptListChangedNotification():
                            logger.debug("MCP server '%s': prompts/list_changed (ignored)", self.name)
                        case ResourceListChangedNotification():
                            logger.debug("MCP server '%s': resources/list_changed (ignored)", self.name)
                        case _:
                            pass
            except Exception:
                logger.exception("Error in MCP message handler for '%s'", self.name)
        return _handler

    async def _refresh_tools(self):
        from tools.registry import registry
        from tools.mcp._registration import _register_server_tools, _forget_mcp_tool_server
        from tools.mcp._schema import sanitize_mcp_name_component

        async with self._refresh_lock:
            old_tool_names = set(self._registered_tool_names)
            async with self._rpc_lock:
                tools_result = await self.session.list_tools()
            new_mcp_tools = tools_result.tools if hasattr(tools_result, "tools") else []
            safe_server = sanitize_mcp_name_component(self.name)

            stale_tool_names = old_tool_names - {
                f"mcp_{safe_server}_{sanitize_mcp_name_component(tool.name)}"
                for tool in new_mcp_tools
            }
            for tool_name in stale_tool_names:
                registry.deregister(tool_name)
                _forget_mcp_tool_server(tool_name)

            self._tools = new_mcp_tools
            self._registered_tool_names = _register_server_tools(self.name, self, self._config)

            new_tool_names = set(self._registered_tool_names)
            added = new_tool_names - old_tool_names
            removed = old_tool_names - new_tool_names
            changes = []
            if added:
                changes.append(f"added: {', '.join(sorted(added))}")
            if removed:
                changes.append(f"removed: {', '.join(sorted(removed))}")
            if changes:
                logger.warning("MCP server '%s': tools changed dynamically — %s.", self.name, "; ".join(changes))
            else:
                logger.info("MCP server '%s': dynamically refreshed %d tool(s) (no changes)", self.name, len(self._registered_tool_names))

    # ----- Lifecycle management --------------------------------------------

    async def _wait_for_lifecycle_event(self) -> str:
        _KEEPALIVE_INTERVAL = 180

        shutdown_task = asyncio.create_task(self._shutdown_event.wait())
        reconnect_task = asyncio.create_task(self._reconnect_event.wait())
        try:
            while True:
                done, _pending = await asyncio.wait(
                    {shutdown_task, reconnect_task},
                    timeout=_KEEPALIVE_INTERVAL,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if done:
                    break
                if self.session:
                    try:
                        await asyncio.wait_for(self.session.list_tools(), timeout=30.0)
                    except Exception as exc:
                        logger.warning("MCP server '%s' keepalive failed, triggering reconnect: %s", self.name, exc)
                        self._reconnect_event.set()
                        break
        finally:
            for t in (shutdown_task, reconnect_task):
                if not t.done():
                    t.cancel()
                    try:
                        await t
                    except (asyncio.CancelledError, Exception):
                        pass

        if self._shutdown_event.is_set():
            return "shutdown"
        self._reconnect_event.clear()
        return "reconnect"

    # ----- Stdio transport -------------------------------------------------

    async def _run_stdio(self, config: dict):
        if not _MCP_AVAILABLE:
            raise ImportError(
                f"MCP server '{self.name}' requires the 'mcp' Python SDK, but "
                "it is not installed. Install with:\n  pip install 'gogeta-agent[mcp]'"
            )

        command = config.get("command")
        args = config.get("args", [])
        user_env = config.get("env")
        if not command:
            raise ValueError(f"MCP server '{self.name}' has no 'command' in config")

        safe_env = _build_safe_env(user_env)
        command, safe_env = _resolve_stdio_command(command, safe_env)

        from tools.osv_check import check_package_for_malware
        malware_error = check_package_for_malware(command, args)
        if malware_error:
            raise ValueError(f"MCP server '{self.name}': {malware_error}")

        server_params = StdioServerParameters(
            command=command, args=args, env=safe_env if safe_env else None,
        )
        sampling_kwargs = self._sampling.session_kwargs() if self._sampling else {}
        if _MCP_NOTIFICATION_TYPES and _MCP_MESSAGE_HANDLER_SUPPORTED:
            sampling_kwargs["message_handler"] = self._make_message_handler()

        pids_before = _snapshot_child_pids()
        new_pids: set = set()
        _write_stderr_log_header(self.name)
        _errlog = _get_mcp_stderr_log()

        try:
            async with stdio_client(server_params, errlog=_errlog) as (read_stream, write_stream):
                new_pids = _snapshot_child_pids() - pids_before
                if new_pids:
                    new_pgids: Dict[int, int] = {}
                    for _pid in new_pids:
                        try:
                            new_pgids[_pid] = os.getpgid(_pid)
                        except (AttributeError, ProcessLookupError, OSError):
                            pass
                    with _lock:
                        for _pid in new_pids:
                            _stdio_pids[_pid] = self.name
                        _stdio_pgids.update(new_pgids)

                async with ClientSession(read_stream, write_stream, **sampling_kwargs) as session:
                    self.initialize_result = await session.initialize()
                    self.session = session
                    await self._discover_tools()
                    self._ready.set()
                    await self._wait_for_lifecycle_event()
        finally:
            if new_pids:
                from gateway.status import _pid_exists
                _killpg = getattr(os, "killpg", None)
                with _lock:
                    for _pid in list(new_pids):
                        _stdio_pids.pop(_pid, None)
                    for pid in list(new_pids):
                        pid_alive = _pid_exists(pid)
                        pgroup_alive = False
                        pgid = _stdio_pgids.get(pid)
                        if not pid_alive and pgid is not None and _killpg is not None:
                            try:
                                _killpg(pgid, 0)
                                pgroup_alive = True
                            except (ProcessLookupError, PermissionError, OSError):
                                pgroup_alive = False
                        if pid_alive or pgroup_alive:
                            _orphan_stdio_pids.add(pid)
                        else:
                            _stdio_pgids.pop(pid, None)

    # ----- HTTP transport --------------------------------------------------

    _MCP_CONTENT_TYPES = ("application/json", "text/event-stream")

    async def _preflight_content_type(self, url: str, *, headers: Optional[dict] = None, ssl_verify: bool = True, client_cert=None, timeout: float = 5.0) -> None:
        try:
            import httpx as _httpx
        except ImportError:
            return

        client_kwargs: dict = {"verify": ssl_verify, "follow_redirects": True, "timeout": _httpx.Timeout(timeout)}
        if client_cert is not None:
            client_kwargs["cert"] = client_cert
        probe_headers = dict(headers) if headers else {}

        try:
            async with _httpx.AsyncClient(**client_kwargs) as client:
                resp = await client.head(url, headers=probe_headers)
                if resp.status_code in (405, 501):
                    resp = await client.get(url, headers=probe_headers)
        except _httpx.HTTPError:
            return

        if not (200 <= resp.status_code < 300):
            return
        ct_base = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if not ct_base:
            return
        if ct_base in self._MCP_CONTENT_TYPES:
            return
        raise NonMcpEndpointError(
            f"MCP server '{self.name}' at {url} returned Content-Type "
            f"'{ct_base}', not an MCP response (expected one of: "
            f"{', '.join(self._MCP_CONTENT_TYPES)}). The URL most likely "
            "points at a web page rather than an MCP endpoint."
        )

    async def _run_http(self, config: dict):
        if not _MCP_HTTP_AVAILABLE:
            raise ImportError(
                f"MCP server '{self.name}' requires HTTP transport but "
                "mcp.client.streamable_http is not available."
            )

        url = config["url"]
        headers = dict(config.get("headers") or {})
        if not any(key.lower() == "mcp-protocol-version" for key in headers):
            headers["mcp-protocol-version"] = LATEST_PROTOCOL_VERSION
        connect_timeout = config.get("connect_timeout", _DEFAULT_CONNECT_TIMEOUT)
        ssl_verify = config.get("ssl_verify", True)
        client_cert = _resolve_client_cert(self.name, config)

        _oauth_auth = None
        if self._auth_type == "oauth":
            try:
                from tools.mcp_oauth_manager import get_manager
                _oauth_auth = get_manager().get_or_build_provider(self.name, url, config.get("oauth"))
            except Exception as exc:
                logger.warning("MCP OAuth setup failed for '%s': %s", self.name, exc)
                raise

        sampling_kwargs = self._sampling.session_kwargs() if self._sampling else {}
        if _MCP_NOTIFICATION_TYPES and _MCP_MESSAGE_HANDLER_SUPPORTED:
            sampling_kwargs["message_handler"] = self._make_message_handler()

        # SSE transport
        if config.get("transport") == "sse":
            if sse_client is None:
                raise ImportError(f"MCP server '{self.name}' requires SSE transport but sse_client is not available.")
            _sse_kwargs: dict = {
                "url": url, "headers": headers or None,
                "timeout": float(connect_timeout), "sse_read_timeout": 300.0,
            }
            if _oauth_auth is not None:
                _sse_kwargs["auth"] = _oauth_auth
            if client_cert is not None or ssl_verify is not True:
                import httpx as _httpx_mod
                _cert_for_factory = client_cert
                _verify_for_factory = ssl_verify

                def _mcp_http_client_factory(headers=None, timeout=None, auth=None):
                    kwargs: dict = {"follow_redirects": True, "verify": _verify_for_factory}
                    if timeout is not None:
                        kwargs["timeout"] = timeout
                    else:
                        kwargs["timeout"] = _httpx_mod.Timeout(30.0, read=300.0)
                    if headers is not None:
                        kwargs["headers"] = headers
                    if auth is not None:
                        kwargs["auth"] = auth
                    if _cert_for_factory is not None:
                        kwargs["cert"] = _cert_for_factory
                    return _httpx_mod.AsyncClient(**kwargs)

                _sse_kwargs["httpx_client_factory"] = _mcp_http_client_factory

            async with sse_client(**_sse_kwargs) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream, **sampling_kwargs) as session:
                    self.initialize_result = await session.initialize()
                    self.session = session
                    await self._discover_tools()
                    self._ready.set()
                    reason = await self._wait_for_lifecycle_event()
                    if reason == "reconnect":
                        logger.info("MCP server '%s': reconnect requested — tearing down SSE session", self.name)
            return

        # Streamable HTTP
        if _MCP_NEW_HTTP:
            import httpx
            _original_url = httpx.URL(url)

            async def _strip_auth_on_cross_origin_redirect(response):
                if response.is_redirect and response.next_request:
                    target = response.next_request.url
                    if (target.scheme, target.host, target.port) != (_original_url.scheme, _original_url.host, _original_url.port):
                        response.next_request.headers.pop("authorization", None)
                        response.next_request.headers.pop("Authorization", None)

            client_kwargs: dict = {
                "follow_redirects": True,
                "timeout": httpx.Timeout(float(connect_timeout), read=300.0),
                "verify": ssl_verify,
                "event_hooks": {"response": [_strip_auth_on_cross_origin_redirect]},
            }
            if headers:
                client_kwargs["headers"] = headers
            if _oauth_auth is not None:
                client_kwargs["auth"] = _oauth_auth
            if client_cert is not None:
                client_kwargs["cert"] = client_cert

            async with httpx.AsyncClient(**client_kwargs) as http_client:
                async with streamable_http_client(url, http_client=http_client) as (read_stream, write_stream, _get_session_id):
                    async with ClientSession(read_stream, write_stream, **sampling_kwargs) as session:
                        self.initialize_result = await session.initialize()
                        self.session = session
                        await self._discover_tools()
                        self._ready.set()
                        reason = await self._wait_for_lifecycle_event()
                        if reason == "reconnect":
                            logger.info("MCP server '%s': reconnect requested — tearing down HTTP session", self.name)
        else:
            _http_kwargs: dict = {"headers": headers, "timeout": float(connect_timeout), "verify": ssl_verify}
            if _oauth_auth is not None:
                _http_kwargs["auth"] = _oauth_auth
            async with streamablehttp_client(url, **_http_kwargs) as (read_stream, write_stream, _get_session_id):
                async with ClientSession(read_stream, write_stream, **sampling_kwargs) as session:
                    self.initialize_result = await session.initialize()
                    self.session = session
                    await self._discover_tools()
                    self._ready.set()
                    reason = await self._wait_for_lifecycle_event()
                    if reason == "reconnect":
                        logger.info("MCP server '%s': reconnect requested — tearing down legacy HTTP session", self.name)

    async def _discover_tools(self):
        if self.session is None:
            return
        async with self._rpc_lock:
            tools_result = await self.session.list_tools()
        self._tools = tools_result.tools if hasattr(tools_result, "tools") else []

    # ----- Main run loop ---------------------------------------------------

    async def run(self, config: dict):
        self._config = config
        self.tool_timeout = config.get("timeout", _DEFAULT_TOOL_TIMEOUT)
        self._auth_type = (config.get("auth") or "").lower().strip()

        sampling_config = config.get("sampling", {})
        if sampling_config.get("enabled", True) and _MCP_SAMPLING_TYPES:
            self._sampling = SamplingHandler(self.name, sampling_config)
        else:
            self._sampling = None

        if "url" in config and "command" in config:
            logger.warning("MCP server '%s' has both 'url' and 'command'. Using HTTP.", self.name)

        if self._is_http():
            try:
                _validate_remote_mcp_url(self.name, config.get("url"))
            except InvalidMcpUrlError as exc:
                logger.warning("%s", exc)
                self._error = exc
                self._ready.set()
                return

            if config.get("transport") != "sse":
                try:
                    await self._preflight_content_type(
                        config["url"],
                        headers=dict(config.get("headers") or {}),
                        ssl_verify=config.get("ssl_verify", True),
                        client_cert=_resolve_client_cert(self.name, config),
                    )
                except NonMcpEndpointError as exc:
                    logger.warning("%s", exc)
                    self._error = exc
                    self._ready.set()
                    return

        retries = 0
        initial_retries = 0
        backoff = 1.0

        while True:
            try:
                if self._is_http():
                    await self._run_http(config)
                else:
                    await self._run_stdio(config)

                if self._shutdown_event.is_set():
                    break
                logger.info("MCP server '%s': reconnecting (OAuth recovery or manual refresh)", self.name)
                self.session = None
                continue

            except asyncio.CancelledError:
                self.session = None
                raise
            except Exception as exc:
                self.session = None
                if not self._ready.is_set():
                    if _is_auth_error(exc):
                        logger.warning("MCP server '%s' failed initial OAuth, not retrying: %s", self.name, exc)
                        self._error = exc
                        self._ready.set()
                        return
                    initial_retries += 1
                    if initial_retries > _MAX_INITIAL_CONNECT_RETRIES:
                        logger.warning("MCP server '%s' failed after %d attempts: %s", self.name, _MAX_INITIAL_CONNECT_RETRIES, exc)
                        self._error = exc
                        self._ready.set()
                        return
                    logger.warning("MCP server '%s' initial connection failed (attempt %d/%d), retrying in %.0fs: %s", self.name, initial_retries, _MAX_INITIAL_CONNECT_RETRIES, backoff, exc)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)
                    if self._shutdown_event.is_set():
                        self._error = exc
                        self._ready.set()
                        return
                    continue

                if self._shutdown_event.is_set():
                    return
                retries += 1
                if retries > _MAX_RECONNECT_RETRIES:
                    logger.warning("MCP server '%s' failed after %d reconnection attempts: %s", self.name, _MAX_RECONNECT_RETRIES, exc)
                    return
                logger.warning("MCP server '%s' connection lost (attempt %d/%d), reconnecting in %.0fs: %s", self.name, retries, _MAX_RECONNECT_RETRIES, backoff, exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)
                if self._shutdown_event.is_set():
                    return
            finally:
                self.session = None

    async def start(self, config: dict):
        self._task = asyncio.ensure_future(self.run(config))
        await self._ready.wait()
        if self._error:
            raise self._error

    async def shutdown(self):
        from tools.registry import registry
        from tools.mcp._registration import _forget_mcp_tool_server

        self._shutdown_event.set()
        self._reconnect_event.set()
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=10)
            except asyncio.TimeoutError:
                logger.warning("MCP server '%s' shutdown timed out, cancelling task", self.name)
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        if self._pending_refresh_tasks:
            for task in list(self._pending_refresh_tasks):
                task.cancel()
            await asyncio.gather(*self._pending_refresh_tasks, return_exceptions=True)
            self._pending_refresh_tasks.clear()
        for tool_name in list(getattr(self, "_registered_tool_names", [])):
            registry.deregister(tool_name)
            _forget_mcp_tool_server(tool_name)
        self._registered_tool_names = []
        self.session = None
