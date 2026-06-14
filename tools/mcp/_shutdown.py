import logging
import os
import signal
from typing import Dict, Optional

from tools.mcp._state import _servers, _lock, _stdio_pids, _stdio_pgids, logger

logger = logging.getLogger(__name__)


def _disconnect_sync(server_name: str) -> None:
    with _lock:
        server = _servers.pop(server_name, None)

    if server is None:
        return

    session = getattr(server, "session", None)
    pid = _stdio_pids.pop(server_name, None)
    pgid = _stdio_pgids.pop(server_name, None)

    if session is not None:
        try:
            session._exit_stack.__aexit__(None, None, None)
        except Exception:
            pass

    if pid is not None:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    if pgid is not None:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, AttributeError):
            pass

    logger.debug("Disconnected MCP server: %s", server_name)


def _disconnect_all_sync() -> None:
    server_names = list(_servers.keys())
    for name in server_names:
        _disconnect_sync(name)


async def _disconnect_server_async(server_name: str) -> None:
    _disconnect_sync(server_name)


async def _disconnect_all_servers_async() -> None:
    _disconnect_all_sync()


def _get_connected_server_names() -> list:
    with _lock:
        return list(_servers.keys())


def _is_server_connected(server_name: str) -> bool:
    with _lock:
        return server_name in _servers
