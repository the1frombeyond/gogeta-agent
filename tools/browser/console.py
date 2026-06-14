import json
import logging

from tools.browser._state import logger
from tools.browser._session import _last_session_key, _get_session_info
from tools.browser._exec import _run_browser_command
from tools.browser._engine import _copy_fallback_warning

logger = logging.getLogger(__name__)


def browser_console(
    clear: bool = False,
    expression: str | None = None,
    task_id: str | None = None,
) -> str:
    session_key = _last_session_key(task_id)

    from tools.browser_camofox import is_camofox_mode as _is_camofox_mode
    if _is_camofox_mode():
        return _camofox_eval(expression or "", task_id)

    if clear:
        result = _run_browser_command(session_key, "console", ["--clear"])
        return json.dumps({"success": result.get("success", False)})

    if expression:
        return _browser_eval(expression, task_id)

    result = _run_browser_command(session_key, "console", [])
    response = {"success": result.get("success", False)}
    if result.get("data", {}).get("messages"):
        response["messages"] = result["data"]["messages"]
    if result.get("data", {}).get("errors"):
        response["errors"] = result["data"]["errors"]
    _copy_fallback_warning(response, result)
    return json.dumps(response)


def _browser_eval(expression: str, task_id: str | None = None) -> str:
    session_key = _last_session_key(task_id)
    result = _run_browser_command(session_key, "eval", [expression])
    response = {"success": result.get("success", False)}
    if result.get("data", {}).get("result"):
        response["result"] = result["data"]["result"]
    if result.get("error"):
        response["error"] = result["error"]
    _copy_fallback_warning(response, result)
    return json.dumps(response)


def _camofox_eval(expression: str, task_id: str | None = None) -> str:
    try:
        from tools.browser_camofox import camofox_eval
        return camofox_eval(expression, task_id)
    except ImportError:
        return json.dumps({"success": False, "error": "Camofox not available"})
