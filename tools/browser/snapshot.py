import json
import logging

from tools.browser._state import logger
from tools.browser._session import _last_session_key
from tools.browser._exec import _run_browser_command
from tools.browser._content import _extract_relevant_content
from tools.browser._engine import _copy_fallback_warning

logger = logging.getLogger(__name__)


def browser_snapshot(
    full: bool = False,
    task_id: str | None = None,
    user_task: str | None = None,
) -> str:
    session_key = _last_session_key(task_id)

    from tools.browser_camofox import is_camofox_mode as _is_camofox_mode
    if _is_camofox_mode():
        from tools.browser_camofox import camofox_snapshot
        result = camofox_snapshot(task_id)
        return json.dumps(result)

    result = _run_browser_command(session_key, "snapshot", [])

    if not result.get("success"):
        return json.dumps({"success": False, "error": result.get("error", "Failed to get snapshot")})

    data = result.get("data", {}) or {}
    snapshot_text = data.get("snapshot", data.get("content", ""))
    refs = data.get("refs", [])
    url = data.get("url", "")
    title = data.get("title", "")

    if snapshot_text and (user_task or (not full and len(snapshot_text) > 8000)):
        snapshot_text = _extract_relevant_content(snapshot_text, user_task)

    response = {
        "success": True,
        "content": snapshot_text,
        "refs": refs,
        "url": url,
        "title": title,
    }

    _copy_fallback_warning(response, result)

    return json.dumps(response)
