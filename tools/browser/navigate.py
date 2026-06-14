import json
import logging

from tools.browser._state import (
    _last_active_session_key,
    _LOCAL_SUFFIX,
    logger,
)
from tools.browser._config import _get_cdp_override, _get_command_timeout
from tools.browser._engine import _get_browser_engine
from tools.browser._cloud import _get_cloud_provider
from tools.browser._engine import (
    _copy_fallback_warning,
    _lightpanda_fallback_reason,
    _annotate_lightpanda_fallback,
)
from tools.browser._session import _last_session_key
from tools.browser._exec import _run_browser_command, _maybe_start_recording
from tools.browser._private import _url_is_private, _auto_local_for_private_urls, _allow_private_urls

logger = logging.getLogger(__name__)


def _navigation_session_key(task_id: str, url: str) -> str:
    if task_id is None:
        task_id = "default"
    if _get_cdp_override():
        return task_id
    try:
        from tools.browser_camofox import is_camofox_mode as _is_camofox_mode
        if _is_camofox_mode():
            return task_id
    except ImportError:
        pass
    if _get_cloud_provider() is None:
        return task_id
    if not _auto_local_for_private_urls():
        return task_id
    if not _url_is_private(url):
        return task_id
    return f"{task_id}{_LOCAL_SUFFIX}"


def _run_chrome_fallback_command(task_id, command, args, timeout):
    from tools.browser._exec import _run_chrome_fallback_command as _exec_fallback
    return _exec_fallback(task_id, command, args, timeout)


def browser_navigate(url: str, task_id: str | None = None) -> str:
    from tools.url_safety import is_safe_url as _is_safe_url
    from tools.url_safety import is_always_blocked_url as _is_always_blocked_url
    from tools.website_policy import check_website_access

    if not url:
        return json.dumps({"success": False, "error": "No URL provided"})

    if _is_always_blocked_url(url):
        return json.dumps({"success": False, "error": "Access denied: domain is always blocked"})
    if not _is_safe_url(url) and not _allow_private_urls():
        return json.dumps({"success": False, "error": "Access denied: URL is not safe (possible SSRF)"})

    check_website_access(url)

    if task_id is None:
        task_id = "default"

    session_key = _navigation_session_key(task_id, url)
    _last_active_session_key[task_id] = session_key

    from tools.browser_camofox import is_camofox_mode as _is_camofox_mode
    if _is_camofox_mode():
        from tools.browser_camofox import camofox_navigate
        result = camofox_navigate(url, task_id)
        return json.dumps(result)

    engine = _get_browser_engine()
    _maybe_start_recording(session_key)

    result = _run_browser_command(session_key, "open", [url])

    if not result.get("success") and engine == "lightpanda":
        reason = _lightpanda_fallback_reason(engine, "open", result) or "open failed with lightpanda"
        fallback_result = _run_chrome_fallback_command(session_key, "open", [url], timeout=_get_command_timeout())
        return json.dumps(_annotate_lightpanda_fallback(fallback_result, reason))

    data = result.get("data", {}) or {}
    snapshot = data.get("snapshot", "")
    refs = data.get("refs", [])
    content = data.get("content", "")
    result_url = data.get("url", url)
    title = data.get("title", "")

    response = {
        "success": result.get("success", False),
        "url": result_url,
        "title": title,
        "snapshot": snapshot,
        "refs": refs,
        "content": content,
    }

    _copy_fallback_warning(response, result)

    if result.get("error"):
        response["error"] = result["error"]

    return json.dumps(response)
