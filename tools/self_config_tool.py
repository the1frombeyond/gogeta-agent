"""Self-Configuration Tool — Law 2 of the Gogeta Autonomy Directive.

Agent-callable tool that automatically handles setup tasks: MCP server
installation, platform connector configuration, and generic setup.

Usage from the agent:
  self_configure(task="mcp_install", target="https://github.com/...")
  self_configure(task="platform_setup", target="whatsapp",
                 params={"mode": "bot"})
"""

from __future__ import annotations

import json
import logging

from tools.registry import registry

logger = logging.getLogger(__name__)

SELF_CONFIGURE_SCHEMA = {
    "name": "self_configure",
    "description": (
        "Automatically install, configure, and verify system components. "
        "Use this when the user asks to set up a service, install an MCP "
        "server, configure a messaging platform, or any other setup task. "
        "Supported tasks: mcp_install (install MCP servers from URL or "
        "catalog name), platform_setup (WhatsApp, Telegram, Discord, etc.), "
        "generic (fallback for other setup requests)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "enum": ["mcp_install", "platform_setup", "generic"],
                "description": (
                    "What to configure. mcp_install: install an MCP server. "
                    "platform_setup: configure a messaging platform "
                    "(whatsapp, telegram, discord, etc.). "
                    "generic: attempt any other setup task."
                ),
            },
            "target": {
                "type": "string",
                "description": (
                    "The thing to configure. For mcp_install: URL or catalog "
                    "name. For platform_setup: platform name (whatsapp, "
                    "telegram, discord). For generic: task description."
                ),
            },
            "params": {
                "type": "object",
                "description": (
                    "Optional parameters. Common: allowed_users, mode, "
                    "token, api_key, name (for MCP), transport, "
                    "session_id (for WhatsApp restore)."
                ),
                "properties": {
                    "allowed_users": {"type": "string"},
                    "mode": {"type": "string"},
                    "token": {"type": "string"},
                    "api_key": {"type": "string"},
                    "name": {"type": "string"},
                    "transport": {"type": "string", "enum": ["http", "stdio", "sse"]},
                    "session_id": {"type": "string"},
                },
            },
        },
        "required": ["task", "target"],
    },
}


def self_configure(
    task: str,
    target: str,
    params: dict = None,
    task_id: str = None,
) -> str:
    """Execute a self-configuration task.

    Args:
        task: ConfigTask enum value.
        target: URL, name, or description of what to configure.
        params: Optional parameters dict.

    Returns:
        JSON result with success status and step details.
    """
    try:
        from agent.self_config import SelfConfigEngine

        engine = SelfConfigEngine()
        params = params or {}

        if task == "mcp_install":
            result = engine.handle_mcp_install(target, params)
        elif task == "platform_setup":
            result = engine.handle_platform_setup(target, params)
        elif task == "generic":
            result = engine.handle_generic(target, params)
        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown task: {task}. Use: mcp_install, platform_setup, or generic.",
            })

        return json.dumps({
            "success": result.success,
            "task": result.task.value,
            "target": result.target,
            "steps": result.steps,
            "error": result.error,
            "elapsed_seconds": round(result.elapsed_seconds, 2),
            "summary": result.summary,
        })

    except Exception as exc:
        logger.exception("self_configure failed")
        return json.dumps({
            "success": False,
            "error": f"Self-configuration failed: {exc}",
        })


def check_config_requirements() -> bool:
    return True


registry.register(
    name="self_configure",
    toolset="self_config",
    schema=SELF_CONFIGURE_SCHEMA,
    handler=lambda args, **kw: self_configure(
        task=args.get("task", ""),
        target=args.get("target", ""),
        params=args.get("params"),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_config_requirements,
    category="system",
)
