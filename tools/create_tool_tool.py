"""create_tool — Autonomous tool creation tool.

Provides two agent-callable tools:

1. ``create_tool`` — Generate, register, test, and wire a new tool from
   a natural-language description. Used when the agent identifies a
   missing capability.

2. ``detect_missing_tools`` — Scan recent conversation for capability
   gaps and suggest new tools to create.

Both delegate to ``agent/tool_creator.py`` (ToolCreatorEngine) for the
heavy lifting. The engine handles code generation, registry registration,
toolset wiring, testing, and documentation.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from tools.registry import registry

logger = logging.getLogger(__name__)

_ENGINE = None


def _get_engine():
    """Lazy-init the ToolCreatorEngine singleton."""
    global _ENGINE
    if _ENGINE is None:
        from agent.tool_creator import ToolCreatorEngine
        from agent.auxiliary_client import call_llm
        _ENGINE = ToolCreatorEngine(call_llm=call_llm)
    return _ENGINE


# ── Tool: create_tool ────────────────────────────────────────────────

CREATE_TOOL_SCHEMA = {
    "name": "create_tool",
    "description": "Create a new tool from a natural-language description. "
                   "Generates Python code, registers it, tests it, and wires it into a toolset.",
    "parameters": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "What the tool should do — be specific about inputs, outputs, and behavior.",
            },
            "tool_name": {
                "type": "string",
                "description": "Snake_case name for the new tool (e.g. 'github_issue_fetcher'). Must be unique.",
            },
            "toolset": {
                "type": "string",
                "description": "Toolset to add the tool to. Defaults to 'user_created'.",
            },
            "auto_test": {
                "type": "boolean",
                "description": "Whether to test after registration (default: true).",
            },
        },
        "required": ["description", "tool_name"],
    },
}


def _create_tool_handler(
    description: str,
    tool_name: str,
    toolset: str = "user_created",
    auto_test: bool = True,
) -> str:
    engine = _get_engine()
    result = engine.create_tool(
        description=description,
        tool_name=tool_name,
        toolset=toolset,
        auto_test=auto_test,
    )
    return json.dumps(result, indent=2)


# ── Tool: detect_missing_tools ──────────────────────────────────────

DETECT_MISSING_TOOLS_SCHEMA = {
    "name": "detect_missing_tools",
    "description": "Analyze recent conversation for missing capabilities that "
                   "would benefit from a new tool.",
    "parameters": {
        "type": "object",
        "properties": {
            "context": {
                "type": "string",
                "description": "Recent conversation text or summary to scan for missing capabilities.",
            },
        },
        "required": ["context"],
    },
}


def _detect_missing_tools_handler(context: str) -> str:
    engine = _get_engine()
    suggestions = engine.detect_missing_capabilities(context)
    if not suggestions:
        return json.dumps({
            "success": True,
            "suggestions": [],
            "message": "No missing capabilities detected.",
        })
    return json.dumps({
        "success": True,
        "suggestions": suggestions,
        "message": f"Found {len(suggestions)} potential missing capabilities. "
                   f"Use create_tool to build any of them.",
    }, indent=2)


# ── Registration ────────────────────────────────────────────────────

def _check_fn() -> bool:
    try:
        from agent.auxiliary_client import call_llm
        return call_llm is not None
    except Exception:
        return False


registry.register(
    name="create_tool",
    toolset="user_created",
    schema=CREATE_TOOL_SCHEMA,
    handler=lambda args, **kw: _create_tool_handler(
        description=args.get("description", ""),
        tool_name=args.get("tool_name", ""),
        toolset=args.get("toolset", "user_created"),
        auto_test=args.get("auto_test", True),
    ),
    check_fn=_check_fn,
    category="development",
)

registry.register(
    name="detect_missing_tools",
    toolset="user_created",
    schema=DETECT_MISSING_TOOLS_SCHEMA,
    handler=lambda args, **kw: _detect_missing_tools_handler(
        context=args.get("context", ""),
    ),
    check_fn=_check_fn,
    category="development",
)
