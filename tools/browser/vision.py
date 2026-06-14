import json
import logging
import os

from typing import Union

from tools.browser._state import _recording_sessions, logger
from tools.browser._session import _last_session_key
from tools.browser._exec import _run_browser_command, _maybe_start_recording, _maybe_stop_recording
from tools.browser._content import _extract_relevant_content
from tools.browser._config import _get_vision_model
from tools.browser._engine import _copy_fallback_warning

logger = logging.getLogger(__name__)


def browser_get_images(task_id: str | None = None) -> str:
    session_key = _last_session_key(task_id)
    result = _run_browser_command(session_key, "screenshot", [])
    if result.get("success"):
        path = result.get("data", {}).get("path", "")
        if path and os.path.isfile(path):
            from tools.vision_tools import describe_image_file
            descriptions = describe_image_file(path)
            return json.dumps({"success": True, "images": descriptions, "path": path})
        return json.dumps({"success": True, "path": path, "images": []})
    return json.dumps({"success": False, "error": result.get("error", "Failed to get images")})


def browser_vision(
    question: str,
    annotate: bool = False,
    task_id: str | None = None,
) -> Union[str, dict]:
    session_key = _last_session_key(task_id)
    vision_model = _get_vision_model()
    if not vision_model:
        return json.dumps({
            "success": False,
            "error": "No vision model configured. Set AUXILIARY_VISION_MODEL env var."
        })

    if annotate:
        result = _run_browser_command(session_key, "screenshot", ["--annotate"])
    else:
        result = _run_browser_command(session_key, "screenshot", [])

    if not result.get("success"):
        return json.dumps({"success": False, "error": result.get("error", "Screenshot failed")})

    screenshot_path = result.get("data", {}).get("path", "")
    if not screenshot_path or not os.path.isfile(screenshot_path):
        return json.dumps({"success": False, "error": "Screenshot file not found"})

    try:
        from agent.auxiliary_client import call_llm
        import base64
        with open(screenshot_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                ],
            }
        ]
        llm_response = call_llm(messages=messages, model=vision_model, max_tokens=4096)
        answer = llm_response.get("content", "").strip()
        return json.dumps({"success": True, "answer": answer, "screenshot_path": screenshot_path})
    except Exception as e:
        logger.warning("Vision analysis failed: %s", e)
        return json.dumps({"success": False, "error": f"Vision analysis failed: {e}"})
