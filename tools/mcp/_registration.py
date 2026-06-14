import logging
from typing import Any, Dict, List

from tools.mcp._state import (
    _servers, _lock, _mcp_tool_server_names, _parallel_safe_servers,
    _UTILITY_CAPABILITY_METHODS, _UTILITY_CAPABILITY_ATTRS,
    _get_server_by_name, _SESSION_EXPIRED_MARKERS,
    logger,
)
from tools.mcp._schema import (
    sanitize_mcp_name_component, _convert_mcp_schema, _build_utility_schemas,
    _normalize_name_filter, _parse_boolish, _check_mcp_tool_injection,
)
from tools.mcp._transport import _format_connect_error, _resolve_client_cert

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool-to-server name tracking
# ---------------------------------------------------------------------------


def _track_mcp_tool_server(tool_name: str, server_name: str) -> None:
    safe_server_name = sanitize_mcp_name_component(server_name)
    with _lock:
        _mcp_tool_server_names[tool_name] = safe_server_name


def _forget_mcp_tool_server(tool_name: str) -> None:
    with _lock:
        _mcp_tool_server_names.pop(tool_name, None)


def _get_server_for_tool(tool_name: str) -> str | None:
    with _lock:
        return _mcp_tool_server_names.get(tool_name)


def _existing_tool_names() -> List[str]:
    names: List[str] = []
    for _sname, server in _servers.items():
        if hasattr(server, "_registered_tool_names"):
            names.extend(server._registered_tool_names)
            continue
        for mcp_tool in server._tools:
            schema = _convert_mcp_schema(server.name, mcp_tool)
            names.append(schema["name"])
    return names


def _get_connected_server_info() -> List[dict]:
    with _lock:
        return [
            {
                "name": s.name,
                "tools": list(getattr(s, "_registered_tool_names", [])),
                "connected": s.session is not None,
                "error": str(s._error) if s._error else None,
            }
            for s in _servers.values()
        ]


# ---------------------------------------------------------------------------
# Handler factories
# ---------------------------------------------------------------------------


def _make_check_fn(server_name: str):
    def _check() -> bool:
        srv = _get_server_by_name(server_name)
        return srv is not None and srv.session is not None
    return _check


def _make_tool_handler(server_name: str, tool_name: str, timeout: float):
    from tools.mcp._handlers import _handle_mcp_tool_call
    def _handler(args: dict, task_id: str = None, **kw) -> str:
        safe_server = sanitize_mcp_name_component(server_name)
        safe_tool = sanitize_mcp_name_component(tool_name)
        return _handle_mcp_tool_call(safe_server, safe_tool, args, timeout, task_id)
    return _handler


def _make_list_resources_handler(server_name: str, timeout: float):
    from tools.mcp._handlers import _handle_list_resources
    safe_name = sanitize_mcp_name_component(server_name)
    return lambda args, task_id=None, **kw: _handle_list_resources(safe_name, timeout, task_id)


def _make_read_resource_handler(server_name: str, timeout: float):
    from tools.mcp._handlers import _handle_read_resource
    safe_name = sanitize_mcp_name_component(server_name)
    return lambda args, task_id=None, **kw: _handle_read_resource(safe_name, args.get("uri", ""), timeout, task_id)


def _make_list_prompts_handler(server_name: str, timeout: float):
    from tools.mcp._handlers import _handle_list_prompts
    safe_name = sanitize_mcp_name_component(server_name)
    return lambda args, task_id=None, **kw: _handle_list_prompts(safe_name, timeout, task_id)


def _make_get_prompt_handler(server_name: str, timeout: float):
    from tools.mcp._handlers import _handle_get_prompt
    safe_name = sanitize_mcp_name_component(server_name)
    return lambda args, task_id=None, **kw: _handle_get_prompt(safe_name, args.get("name", ""), args.get("arguments"), timeout, task_id)


# ---------------------------------------------------------------------------
# Utility schema selection
# ---------------------------------------------------------------------------


def _select_utility_schemas(server_name: str, server, config: dict) -> List[dict]:
    tools_filter = config.get("tools") or {}
    resources_enabled = _parse_boolish(
        tools_filter.get("resources") if isinstance(tools_filter, dict) else None,
        default=True,
    )
    prompts_enabled = _parse_boolish(
        tools_filter.get("prompts") if isinstance(tools_filter, dict) else None,
        default=True,
    )

    advertised_caps = None
    init_result = getattr(server, "initialize_result", None)
    if init_result is not None:
        advertised_caps = getattr(init_result, "capabilities", None)

    selected: List[dict] = []
    for entry in _build_utility_schemas(server_name):
        handler_key = entry["handler_key"]
        if handler_key in {"list_resources", "read_resource"} and not resources_enabled:
            continue
        if handler_key in {"list_prompts", "get_prompt"} and not prompts_enabled:
            continue

        if advertised_caps is not None:
            cap_attr = _UTILITY_CAPABILITY_ATTRS[handler_key]
            if getattr(advertised_caps, cap_attr, None) is None:
                continue
        else:
            required_method = _UTILITY_CAPABILITY_METHODS[handler_key]
            if not hasattr(server.session, required_method):
                continue
        selected.append(entry)
    return selected


# ---------------------------------------------------------------------------
# Server tool registration
# ---------------------------------------------------------------------------


def _register_server_tools(name: str, server, config: dict) -> List[str]:
    from tools.registry import registry

    registered_names: List[str] = []
    toolset_name = f"mcp-{name}"
    tools_filter = config.get("tools") or {}
    include_set = _normalize_name_filter(
        tools_filter.get("include") if isinstance(tools_filter, dict) else None,
        f"mcp_servers.{name}.tools.include",
    )
    exclude_set = _normalize_name_filter(
        tools_filter.get("exclude") if isinstance(tools_filter, dict) else None,
        f"mcp_servers.{name}.tools.exclude",
    )

    def _should_register(tool_name: str) -> bool:
        if include_set:
            return tool_name in include_set
        if exclude_set:
            return tool_name not in exclude_set
        return True

    for mcp_tool in server._tools:
        if not _should_register(mcp_tool.name):
            continue
        _check_mcp_tool_injection(name, mcp_tool.name, mcp_tool.description or "")
        schema = _convert_mcp_schema(name, mcp_tool)
        tool_name_prefixed = schema["name"]
        existing_toolset = registry.get_toolset_for_tool(tool_name_prefixed)
        if existing_toolset and not existing_toolset.startswith("mcp-"):
            continue

        registry.register(
            name=tool_name_prefixed,
            toolset=toolset_name,
            schema=schema,
            handler=_make_tool_handler(name, mcp_tool.name, server.tool_timeout),
            check_fn=_make_check_fn(name),
            is_async=False,
            description=schema["description"],
        )
        _track_mcp_tool_server(tool_name_prefixed, name)
        registered_names.append(tool_name_prefixed)

    _handler_factories = {
        "list_resources": _make_list_resources_handler,
        "read_resource": _make_read_resource_handler,
        "list_prompts": _make_list_prompts_handler,
        "get_prompt": _make_get_prompt_handler,
    }
    check_fn = _make_check_fn(name)
    for entry in _select_utility_schemas(name, server, config):
        schema = entry["schema"]
        handler_key = entry["handler_key"]
        handler = _handler_factories[handler_key](name, server.tool_timeout)
        util_name = schema["name"]

        existing_toolset = registry.get_toolset_for_tool(util_name)
        if existing_toolset and not existing_toolset.startswith("mcp-"):
            continue

        registry.register(
            name=util_name,
            toolset=toolset_name,
            schema=schema,
            handler=handler,
            check_fn=check_fn,
            is_async=False,
            description=schema.get("description", ""),
        )
        _track_mcp_tool_server(util_name, name)
        registered_names.append(util_name)

    return registered_names


# ---------------------------------------------------------------------------
# Server discovery & registration entry point
# ---------------------------------------------------------------------------


def _session_expired(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(marker in msg for marker in _SESSION_EXPIRED_MARKERS)


def _discover_one(name: str, cfg: dict):
    """Discover and connect a single MCP server."""
    from tools.mcp._server import MCPServerTask
    from tools.mcp._loop import _ensure_mcp_loop, _run_on_mcp_loop

    connect_timeout = cfg.get("connect_timeout", 60)

    with _lock:
        existing = _servers.get(name)
        if existing is not None:
            logger.warning("MCP server '%s' already connected, skipping", name)
            return None

    _ensure_mcp_loop()

    server = MCPServerTask(name)
    with _lock:
        _servers[name] = server

    try:
        _run_on_mcp_loop(server.start(cfg), timeout=connect_timeout + 5)

        with _lock:
            if server._error:
                _servers.pop(name, None)
                return None

        if cfg.get("parallel_safe", False):
            with _lock:
                _parallel_safe_servers.add(sanitize_mcp_name_component(name))
        else:
            with _lock:
                _parallel_safe_servers.discard(sanitize_mcp_name_component(name))

        return server
    except Exception as exc:
        with _lock:
            _servers.pop(name, None)
        logger.warning("MCP server '%s' failed to connect: %s", name, _format_connect_error(exc))
        return None


def _connect_server(name: str, config: dict):
    """Create an MCPServerTask, start it, and return when ready."""
    from tools.mcp._server import MCPServerTask
    server = MCPServerTask(name)
    from tools.mcp._loop import _run_on_mcp_loop
    _run_on_mcp_loop(server.start(config), timeout=config.get("connect_timeout", 60) + 5)
    return server


def _discover_and_register_server(name: str, config: dict) -> List[str]:
    """Connect to a single MCP server, discover tools, and register them.

    Returns list of registered tool names.
    """
    connect_timeout = config.get("connect_timeout", 60)
    server = _connect_server(name, config)
    with _lock:
        _servers[name] = server
    registered_names = _register_server_tools(name, server, config)
    server._registered_tool_names = list(registered_names)
    transport_type = "HTTP" if "url" in config else "stdio"
    logger.info(
        "MCP server '%s' (%s): registered %d tool(s): %s",
        name, transport_type, len(registered_names),
        ", ".join(registered_names),
    )
    return registered_names


def register_mcp_servers(servers: Dict[str, dict]) -> List[str]:
    if not servers:
        return []

    from tools.mcp._loop import _ensure_mcp_loop, _run_on_mcp_loop
    from tools.mcp._server import MCPServerTask

    _ensure_mcp_loop()

    new_servers = {}
    for name, cfg in servers.items():
        with _lock:
            if name in _servers:
                logger.debug("MCP server '%s' already registered, skipping", name)
                continue
        new_servers[name] = cfg

    if not new_servers:
        return list(_servers.keys())

    async def _connect_all():
        import asyncio
        tasks = {}
        for name, cfg in new_servers.items():
            srv = MCPServerTask(name)
            with _lock:
                _servers[name] = srv
            task = asyncio.ensure_future(srv.start(cfg))
            tasks[name] = (srv, task)

        for name, (srv, task) in tasks.items():
            try:
                await asyncio.wait_for(task, timeout=cfg.get("connect_timeout", 60) + 5)
            except Exception as exc:
                with _lock:
                    _servers.pop(name, None)
                logger.warning("MCP server '%s' failed: %s", name, _format_connect_error(exc))

        for name, cfg in new_servers.items():
            with _lock:
                srv = _servers.get(name)
                if srv is None:
                    continue
                if cfg.get("parallel_safe", False):
                    _parallel_safe_servers.add(sanitize_mcp_name_component(name))
                else:
                    _parallel_safe_servers.discard(sanitize_mcp_name_component(name))
                srv._registered_tool_names = _register_server_tools(name, srv, cfg)

        return [n for n in new_servers if n in _servers]

    try:
        return _run_on_mcp_loop(_connect_all(), timeout=90)
    except Exception as exc:
        logger.error("MCP server registration failed: %s", exc)
        return []
