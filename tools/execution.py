"""Tool execution layer — wraps tool invocation with permission checks,
event emission, and error handling.

Callers use ``execute_tool()`` instead of calling ``registry.dispatch()``
directly to get automatic permission gating, timing, event emission, and
success/failure tracking.

Execution emits ``TOOL_STARTED``, ``TOOL_FINISHED``, and ``TOOL_FAILED``
events on the bus instead of calling analytics, cost tracking, or other
systems directly. Subscribers react to those events independently.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def execute_tool(
    name: str,
    args: Dict[str, Any],
    *,
    session_id: str = "",
    agent_id: str = "",
    provider: str = "",
    context: Optional[Dict[str, Any]] = None,
    skip_permissions: bool = False,
    skip_events: bool = False,
) -> str:
    """Execute a tool by name with full permission gating and event emission.

    Arguments:
        name: Registered tool name.
        args: Tool arguments dict.
        session_id: Current session ID for analytics.
        agent_id: Current agent ID for analytics.
        provider: Provider name for cost attribution.
        context: Permission-check context dict.
        skip_permissions: Bypass permission checks (internal calls).
        skip_events: Skip event emission on the bus (internal calls).

    Returns:
        JSON result string (same format as ``registry.dispatch()``).
    """
    from tools.registry import registry
    from tools.permissions import permission_manager

    entry = registry.get_entry(name)
    category = getattr(entry, "category", "") if entry else ""

    if not skip_permissions:
        permitted = permission_manager.check_permission(
            name, context=context or {}, category=category,
        )
        if not permitted:
            return f'{{"error": "Permission denied for tool: {name}"}}'

        approved = await permission_manager.request_approval(
            name, context=context or {}, category=category,
        )
        if not approved:
            return f'{{"error": "Approval denied for tool: {name}"}}'

        permission_manager.record_call(name)

    start = time.monotonic()
    success = True
    error_msg = ""
    result = ""

    if not skip_events:
        _emit_tool_started(name, args, category, session_id, agent_id, provider)

    try:
        result = registry.dispatch(name, args)
        parsed = json.loads(result)
        if "error" in parsed:
            success = False
            error_msg = parsed["error"]
    except Exception as exc:
        success = False
        error_msg = str(exc)
        result = f'{{"error": "Tool execution failed: {exc}"}}'

    duration_ms = (time.monotonic() - start) * 1000

    if not skip_events:
        if success:
            _emit_tool_finished(
                name, category, session_id, agent_id, provider,
                duration_ms, error_msg, args,
            )
        else:
            _emit_tool_failed(
                name, category, session_id, agent_id, provider,
                duration_ms, error_msg, args,
            )

    return result


# ---------------------------------------------------------------------------
# Internal event emitters
# ---------------------------------------------------------------------------

def _emit_tool_started(
    name: str, args: dict, category: str,
    session_id: str, agent_id: str, provider: str,
) -> None:
    try:
        from core.events.bus import event_bus
        from core.events.events import EventType
        event_bus.emit(
            EventType.TOOL_STARTED,
            data={
                "name": name,
                "args": args,
                "category": category,
                "session_id": session_id,
                "agent_id": agent_id,
                "provider": provider,
            },
            source="execution",
        )
    except Exception as exc:
        logger.debug("Failed to emit TOOL_STARTED for '%s': %s", name, exc)


def _emit_tool_finished(
    name: str, category: str,
    session_id: str, agent_id: str, provider: str,
    duration_ms: float, error_msg: str, args: dict,
) -> None:
    try:
        from core.events.bus import event_bus
        from core.events.events import EventType
        event_bus.emit(
            EventType.TOOL_FINISHED,
            data={
                "name": name,
                "category": category,
                "session_id": session_id,
                "agent_id": agent_id,
                "provider": provider,
                "duration_ms": duration_ms,
                "success": True,
                "error": "",
                "args": args,
                "timestamp": time.time(),
            },
            source="execution",
        )
    except Exception as exc:
        logger.debug("Failed to emit TOOL_FINISHED for '%s': %s", name, exc)


def _emit_tool_failed(
    name: str, category: str,
    session_id: str, agent_id: str, provider: str,
    duration_ms: float, error_msg: str, args: dict,
) -> None:
    try:
        from core.events.bus import event_bus
        from core.events.events import EventType
        event_bus.emit(
            EventType.TOOL_FAILED,
            data={
                "name": name,
                "category": category,
                "session_id": session_id,
                "agent_id": agent_id,
                "provider": provider,
                "duration_ms": duration_ms,
                "success": False,
                "error": error_msg[:500],
                "args": args,
                "timestamp": time.time(),
            },
            source="execution",
        )
    except Exception as exc:
        logger.debug("Failed to emit TOOL_FAILED for '%s': %s", name, exc)
