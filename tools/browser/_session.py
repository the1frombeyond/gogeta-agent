import atexit
import logging
import threading
import time
import uuid

from tools.browser._state import (
    _active_sessions,
    _cleanup_lock,
    _cleanup_thread,
    _cleanup_running,
    _last_active_session_key,
    _LOCAL_SUFFIX,
    _session_last_activity,
    BROWSER_SESSION_INACTIVITY_TIMEOUT,
    logger,
)
from tools.browser._config import _get_cdp_override, _resolve_cdp_override

logger = logging.getLogger(__name__)


def _last_session_key(task_id: str) -> str:
    if task_id is None:
        task_id = "default"
    return _last_active_session_key.get(task_id, task_id)


def _is_local_sidecar_key(session_key: str) -> bool:
    return session_key.endswith(_LOCAL_SUFFIX)


def _create_local_session(task_id: str) -> dict[str, str]:
    session_name = f"h_{uuid.uuid4().hex[:10]}"
    logger.info("Created local browser session %s for task %s", session_name, task_id)
    return {
        "session_name": session_name,
        "bb_session_id": None,
        "cdp_url": None,
        "features": {"local": True},
    }


def _create_cdp_session(task_id: str, cdp_url: str) -> dict[str, str]:
    session_name = f"cdp_{uuid.uuid4().hex[:10]}"
    logger.info("Created CDP browser session %s \u2192 %s for task %s", session_name, cdp_url, task_id)
    return {
        "session_name": session_name,
        "bb_session_id": None,
        "cdp_url": cdp_url,
        "features": {"cdp_override": True},
    }


def _get_session_info(task_id: str | None = None) -> dict[str, str]:
    if task_id is None:
        task_id = "default"
    _start_browser_cleanup_thread()
    _update_session_activity(task_id)
    with _cleanup_lock:
        if task_id in _active_sessions:
            return _active_sessions[task_id]
    force_local = _is_local_sidecar_key(task_id)
    cdp_override = _get_cdp_override()
    if cdp_override and not force_local:
        session_info = _create_cdp_session(task_id, cdp_override)
    elif force_local:
        session_info = _create_local_session(task_id)
    else:
        from tools.browser._cloud import _get_cloud_provider
        provider = _get_cloud_provider()
        if provider is None:
            session_info = _create_local_session(task_id)
        else:
            try:
                session_info = provider.create_session(task_id)
                if not session_info or not isinstance(session_info, dict):
                    raise ValueError(f"Cloud provider returned invalid session: {session_info!r}")
                if session_info.get("cdp_url"):
                    session_info = dict(session_info)
                    session_info["cdp_url"] = _resolve_cdp_override(str(session_info["cdp_url"]))
            except Exception as e:
                provider_name = type(provider).__name__
                logger.warning(
                    "Cloud provider %s failed (%s); attempting fallback to local Chromium for task %s",
                    provider_name, e, task_id, exc_info=True,
                )
                try:
                    session_info = _create_local_session(task_id)
                except Exception as local_error:
                    raise RuntimeError(
                        f"Cloud provider {provider_name} failed ({e}) and local "
                        f"fallback also failed ({local_error})"
                    ) from e
                if isinstance(session_info, dict):
                    session_info = dict(session_info)
                    session_info["fallback_from_cloud"] = True
                    session_info["fallback_reason"] = str(e)
                    session_info["fallback_provider"] = provider_name
    with _cleanup_lock:
        if task_id in _active_sessions:
            return _active_sessions[task_id]
        _active_sessions[task_id] = session_info
    if not force_local:
        from tools.browser._cloud import _ensure_cdp_supervisor
        _ensure_cdp_supervisor(task_id)
    return session_info


def _update_session_activity(task_id: str):
    with _cleanup_lock:
        _session_last_activity[task_id] = time.time()


# ---------------------------------------------------------------------------
# Cleanup thread
# ---------------------------------------------------------------------------

def _browser_cleanup_thread_worker():
    try:
        from tools.browser.cleanup import _reap_orphaned_browser_sessions
        _reap_orphaned_browser_sessions()
    except Exception as e:
        logger.warning("Orphan reap error: %s", e)
    while _cleanup_running:
        try:
            _cleanup_inactive_browser_sessions()
        except Exception as e:
            logger.warning("Cleanup thread error: %s", e)
        for _ in range(30):
            if not _cleanup_running:
                break
            time.sleep(1)


def _start_browser_cleanup_thread():
    global _cleanup_thread, _cleanup_running
    with _cleanup_lock:
        if _cleanup_thread is None or not _cleanup_thread.is_alive():
            _cleanup_running = True
            _cleanup_thread = threading.Thread(
                target=_browser_cleanup_thread_worker,
                daemon=True,
                name="browser-cleanup"
            )
            _cleanup_thread.start()
            logger.info("Started inactivity cleanup thread (timeout: %ss)", BROWSER_SESSION_INACTIVITY_TIMEOUT)


def _stop_browser_cleanup_thread():
    global _cleanup_running
    _cleanup_running = False
    if _cleanup_thread is not None:
        _cleanup_thread.join(timeout=5)


def _cleanup_inactive_browser_sessions():
    current_time = time.time()
    sessions_to_cleanup = []
    with _cleanup_lock:
        for task_id, last_time in list(_session_last_activity.items()):
            if current_time - last_time > BROWSER_SESSION_INACTIVITY_TIMEOUT:
                sessions_to_cleanup.append(task_id)
    for task_id in sessions_to_cleanup:
        try:
            elapsed = int(current_time - _session_last_activity.get(task_id, current_time))
            logger.info("Cleaning up inactive session for task: %s (inactive for %ss)", task_id, elapsed)
            from tools.browser.cleanup import cleanup_browser
            cleanup_browser(task_id)
            with _cleanup_lock:
                if task_id in _session_last_activity:
                    del _session_last_activity[task_id]
        except Exception as e:
            logger.warning("Error cleaning up inactive session %s: %s", task_id, e)


atexit.register(_stop_browser_cleanup_thread)
