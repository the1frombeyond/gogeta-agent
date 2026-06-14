import json
import logging

from tools.browser._state import logger
from tools.browser._session import _last_session_key
from tools.browser._exec import _run_browser_command
from tools.browser._engine import _copy_fallback_warning

logger = logging.getLogger(__name__)


def browser_click(ref: str, task_id: str | None = None) -> str:
    session_key = _last_session_key(task_id)
    result = _run_browser_command(session_key, "click", [ref])
    response = {"success": result.get("success", False)}
    if result.get("error"):
        response["error"] = result["error"]
    if result.get("data", {}).get("snapshot"):
        response["snapshot"] = result["data"]["snapshot"]
    _copy_fallback_warning(response, result)
    return json.dumps(response)


def browser_type(ref: str, text: str, task_id: str | None = None) -> str:
    session_key = _last_session_key(task_id)
    result = _run_browser_command(session_key, "fill", [ref, text])
    response = {"success": result.get("success", False)}
    if result.get("error"):
        response["error"] = result["error"]
    _copy_fallback_warning(response, result)
    return json.dumps(response)


def browser_scroll(direction: str = "down", task_id: str | None = None) -> str:
    session_key = _last_session_key(task_id)
    result = _run_browser_command(session_key, "scroll", [direction])
    response = {"success": result.get("success", False)}
    if result.get("error"):
        response["error"] = result["error"]
    _copy_fallback_warning(response, result)
    return json.dumps(response)


def browser_back(task_id: str | None = None) -> str:
    session_key = _last_session_key(task_id)
    result = _run_browser_command(session_key, "back", [])
    response = {"success": result.get("success", False)}
    if result.get("error"):
        response["error"] = result["error"]
    _copy_fallback_warning(response, result)
    return json.dumps(response)


def browser_press(key: str, task_id: str | None = None) -> str:
    session_key = _last_session_key(task_id)
    result = _run_browser_command(session_key, "press", [key])
    response = {"success": result.get("success", False)}
    if result.get("error"):
        response["error"] = result["error"]
    _copy_fallback_warning(response, result)
    return json.dumps(response)
