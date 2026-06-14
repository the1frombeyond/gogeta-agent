import atexit
import glob
import logging
import os
import shutil
import time

from pathlib import Path

from tools.browser._state import (
    _active_sessions,
    _cleanup_done,
    _cleanup_lock,
    _recording_sessions,
    _session_last_activity,
    logger,
)
from tools.browser._exec import _run_browser_command
from tools.browser._session import _get_session_info
from tools.browser._config import _socket_safe_tmpdir

logger = logging.getLogger(__name__)


def _write_owner_pid(socket_dir: str, session_name: str) -> None:
    try:
        path = os.path.join(socket_dir, f"{session_name}.owner_pid")
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError as exc:
        logger.debug("Could not write owner_pid file for %s: %s", session_name, exc)


def _reap_orphaned_browser_sessions():
    tmpdir = _socket_safe_tmpdir()
    pattern = os.path.join(tmpdir, "agent-browser-h_*")
    socket_dirs = glob.glob(pattern)
    socket_dirs += glob.glob(os.path.join(tmpdir, "agent-browser-cdp_*"))
    socket_dirs += glob.glob(os.path.join(tmpdir, "agent-browser-gogeta_*"))
    if not socket_dirs:
        return
    with _cleanup_lock:
        tracked_names = {
            info.get("session_name")
            for info in _active_sessions.values()
            if info.get("session_name")
        }
    reaped = 0
    for socket_dir in socket_dirs:
        dir_name = os.path.basename(socket_dir)
        session_name = dir_name.removeprefix("agent-browser-")
        if not session_name:
            continue
        owner_pid_file = os.path.join(socket_dir, f"{session_name}.owner_pid")
        owner_alive: bool | None = None
        if os.path.isfile(owner_pid_file):
            try:
                owner_pid = int(Path(owner_pid_file).read_text(encoding="utf-8").strip())
                from gateway.status import _pid_exists
                owner_alive = _pid_exists(owner_pid)
            except (ValueError, OSError):
                owner_alive = None
        if owner_alive is True:
            continue
        if owner_alive is None:
            if session_name in tracked_names:
                continue
        pid_file = os.path.join(socket_dir, f"{session_name}.pid")
        if not os.path.isfile(pid_file):
            shutil.rmtree(socket_dir, ignore_errors=True)
            continue
        try:
            daemon_pid = int(Path(pid_file).read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            shutil.rmtree(socket_dir, ignore_errors=True)
            continue
        from gateway.status import _pid_exists
        if not _pid_exists(daemon_pid):
            shutil.rmtree(socket_dir, ignore_errors=True)
            continue
        try:
            from tools.process_registry import ProcessRegistry
            ProcessRegistry._terminate_host_pid(daemon_pid)
            logger.info("Reaped orphaned browser daemon PID %d (session %s)", daemon_pid, session_name)
            reaped += 1
        except (ProcessLookupError, PermissionError, OSError):
            pass
        shutil.rmtree(socket_dir, ignore_errors=True)
    if reaped:
        logger.info("Reaped %d orphaned browser session(s) from previous run(s)", reaped)


def _emergency_cleanup_all_sessions():
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    if _active_sessions:
        logger.info("Emergency cleanup: closing %s active session(s)...", len(_active_sessions))
        try:
            cleanup_all_browsers()
        except Exception as e:
            logger.error("Emergency cleanup error: %s", e)
        finally:
            with _cleanup_lock:
                _active_sessions.clear()
                _session_last_activity.clear()
                _recording_sessions.clear()
    try:
        _reap_orphaned_browser_sessions()
    except Exception as e:
        logger.debug("Orphan reap on exit failed: %s", e)


atexit.register(_emergency_cleanup_all_sessions)


def _cleanup_old_screenshots(screenshots_dir, max_age_hours=24):
    if not os.path.isdir(screenshots_dir):
        return
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    for fname in os.listdir(screenshots_dir):
        if not fname.endswith(".png"):
            continue
        fpath = os.path.join(screenshots_dir, fname)
        try:
            if os.path.getmtime(fpath) < cutoff:
                os.unlink(fpath)
        except OSError:
            pass


def _cleanup_old_recordings(max_age_hours=72):
    from gogeta_constants import get_gogeta_home
    recordings_dir = get_gogeta_home() / "recordings"
    if not recordings_dir.is_dir():
        return
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    for fname in os.listdir(str(recordings_dir)):
        fpath = recordings_dir / fname
        try:
            if fpath.stat().st_mtime < cutoff:
                fpath.unlink()
        except OSError:
            pass


def cleanup_browser(task_id: str | None = None) -> None:
    if task_id is None:
        task_id = "default"
    try:
        _cleanup_single_browser_session(task_id)
    except Exception as e:
        logger.error("Error cleaning up browser %s: %s", task_id, e)


def _cleanup_single_browser_session(task_id: str) -> None:
    session_info = None
    with _cleanup_lock:
        session_info = _active_sessions.pop(task_id, None)
        _session_last_activity.pop(task_id, None)
        _recording_sessions.discard(task_id)
    if not session_info:
        return
    session_name = session_info.get("session_name")
    try:
        if session_name and not session_info.get("cdp_url"):
            _run_browser_command(task_id, "close", [], timeout=10)
            tmpdir = _socket_safe_tmpdir()
            socket_dir = os.path.join(tmpdir, f"agent-browser-{session_name}")
            shutil.rmtree(socket_dir, ignore_errors=True)
    except Exception as e:
        logger.warning("Error closing browser session %s: %s", task_id, e)
    try:
        from tools.browser._cloud import _stop_cdp_supervisor
        _stop_cdp_supervisor(task_id)
    except Exception:
        pass


def cleanup_all_browsers() -> None:
    tasks = list(_active_sessions.keys())
    for task_id in tasks:
        try:
            cleanup_browser(task_id)
        except Exception as e:
            logger.warning("Error cleaning up session %s: %s", task_id, e)
