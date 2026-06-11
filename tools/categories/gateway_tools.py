"""Gateway platform tools — exposes gateway state, connection status,
and platform management as registered tools.

This is a category-based tool module: auto-discovered from
``tools/categories/`` and registered into the central registry.
"""

from tools.metadata import ToolMetadata
from tools.registry import registry

_GATEWAY_TOOLS_METADATA = ToolMetadata(
    version="1.0.0",
    author="Gogeta",
    category="gateway",
    tags=["gateway", "platform", "status", "management"],
    description="Tools for inspecting and managing gateway platform connections",
)


def _gateway_status_tool(args: dict, **kwargs) -> str:
    """Return gateway connection status as JSON."""
    try:
        from gateway.run import _gateway_runner_ref
        runner = _gateway_runner_ref()
        if runner is None:
            return '{"error": "Gateway is not running", "connected": false}'
        platforms = {}
        for platform, adapter in (runner.adapters or {}).items():
            platforms[platform.value] = {
                "connected": adapter.is_connected() if hasattr(adapter, "is_connected") else True,
                "name": platform.value,
            }
        return __import__("json").dumps({
            "connected": True,
            "platforms": platforms,
            "running": getattr(runner, "_running", False),
        }, ensure_ascii=False)
    except Exception as exc:
        return __import__("json").dumps({
            "error": str(exc),
            "connected": False,
        }, ensure_ascii=False)


def _list_registered_tools(args: dict, **kwargs) -> str:
    """List all registered tools grouped by category."""
    from tools.registry import registry as _reg
    entries = _reg._snapshot_entries()
    by_category = {}
    for entry in sorted(entries, key=lambda e: e.name):
        cat = getattr(entry, "category", None) or entry.toolset
        by_category.setdefault(cat, []).append(entry.name)
    return __import__("json").dumps({
        "total": len(entries),
        "categories": {cat: sorted(names) for cat, names in sorted(by_category.items())},
    }, ensure_ascii=False)


registry.register(
    name="gateway_status",
    toolset="gateway",
    schema={
        "name": "gateway_status",
        "description": "Check gateway connection status for all platform adapters.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    handler=_gateway_status_tool,
    category="gateway",
    metadata=_GATEWAY_TOOLS_METADATA,
)

registry.register(
    name="list_tools",
    toolset="gateway",
    schema={
        "name": "list_tools",
        "description": "List all registered tools grouped by category.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    handler=_list_registered_tools,
    category="gateway",
    metadata=_GATEWAY_TOOLS_METADATA,
)
