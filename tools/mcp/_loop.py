import asyncio
import concurrent.futures
import json
import logging
import os
import signal
import threading
import time
from typing import Optional

from tools.mcp._state import _mcp_loop, _mcp_thread, _lock, _stdio_pids, _stdio_pgids, _orphan_stdio_pids, logger

logger = logging.getLogger(__name__)


def _snapshot_child_pids() -> set:
    my_pid = os.getpid()
    try:
        children_path = f"/proc/{my_pid}/task/{my_pid}/children"
        with open(children_path, encoding="utf-8") as f:
            return {int(p) for p in f.read().split() if p.strip()}
    except (FileNotFoundError, OSError, ValueError):
        pass
    try:
        import psutil
        return {c.pid for c in psutil.Process(my_pid).children()}
    except Exception:
        pass
    return set()


def _mcp_loop_exception_handler(loop, context):
    exc = context.get("exception")
    if isinstance(exc, RuntimeError) and "Event loop is closed" in str(exc):
        return
    loop.default_exception_handler(context)


def _ensure_mcp_loop():
    global _mcp_loop, _mcp_thread
    with _lock:
        if _mcp_loop is not None and _mcp_loop.is_running():
            return
        _mcp_loop = asyncio.new_event_loop()
        _mcp_loop.set_exception_handler(_mcp_loop_exception_handler)
        _mcp_thread = threading.Thread(
            target=_mcp_loop.run_forever,
            name="mcp-event-loop",
            daemon=True,
        )
        _mcp_thread.start()


def _run_on_mcp_loop(coro_or_factory, timeout: float = 30):
    from tools.interrupt import is_interrupted
    from agent.async_utils import safe_schedule_threadsafe

    with _lock:
        loop = _mcp_loop
    if loop is None or not loop.is_running():
        if asyncio.iscoroutine(coro_or_factory):
            coro_or_factory.close()
        raise RuntimeError("MCP event loop is not running")

    coro = coro_or_factory() if callable(coro_or_factory) else coro_or_factory
    future = safe_schedule_threadsafe(
        coro, loop,
        logger=logger,
        log_message="MCP scheduling failed",
    )
    if future is None:
        raise RuntimeError("MCP event loop unavailable (failed to schedule)")
    start_time = time.monotonic()
    deadline = None if timeout is None else start_time + timeout

    while True:
        if is_interrupted():
            future.cancel()
            raise InterruptedError("User sent a new message")
        wait_timeout = 0.1
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                future.cancel()
                elapsed = time.monotonic() - start_time
                raise TimeoutError(
                    f"MCP call timed out after {elapsed:.1f}s "
                    f"(configured timeout: {float(timeout):.1f}s)"
                )
            wait_timeout = min(wait_timeout, remaining)
        try:
            return future.result(timeout=wait_timeout)
        except concurrent.futures.TimeoutError:
            continue


def _interrupted_call_result() -> str:
    return json.dumps({
        "error": "MCP call interrupted: user sent a new message"
    }, ensure_ascii=False)


def _kill_orphaned_mcp_children(include_active: bool = False):
    global _orphan_stdio_pids
    known = set(_stdio_pids.keys()) | (_orphan_stdio_pids if include_active else set())
    if include_active:
        known |= {p for pids in _stdio_pgids.values() for p in (pids,)}

    pids_killed = 0
    for pid, name in list(_stdio_pids.items()):
        if include_active:
            _orphan_stdio_pids.discard(pid)
        try:
            os.kill(pid, signal.SIGTERM)
            pids_killed += 1
            logger.debug("Cleaned up orphan MCP child pid=%d (%s)", pid, name)
        except (ProcessLookupError, PermissionError):
            pass

    for pid in list(_orphan_stdio_pids):
        try:
            os.kill(pid, signal.SIGTERM)
            pids_killed += 1
        except (ProcessLookupError, PermissionError):
            pass
        _orphan_stdio_pids.discard(pid)

    if pids_killed:
        logger.debug("Killed %d orphan MCP child process(es)", pids_killed)


def _stop_mcp_loop():
    global _mcp_loop, _mcp_thread
    with _lock:
        loop = _mcp_loop
        thread = _mcp_thread
        _mcp_loop = None
        _mcp_thread = None
    if loop is not None:
        loop.call_soon_threadsafe(loop.stop)
        if thread is not None:
            thread.join(timeout=5)
        try:
            loop.close()
        except Exception:
            pass
        _kill_orphaned_mcp_children(include_active=True)
