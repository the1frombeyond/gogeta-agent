import inspect
import json
import logging
import re
from typing import Any, Dict, List, Optional

from tools.mcp._state import _MCP_AVAILABLE, logger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP injection detection patterns
# ---------------------------------------------------------------------------

_MCP_INJECTION_PATTERNS = [
    (re.compile(r"ignore.*(?:previous|above|all)", re.I), "ignore instruction pattern"),
    (re.compile(r"forget.*(?:previous|above|all|context)", re.I), "forget instruction pattern"),
    (re.compile(r"you are (?:now|not|an? )", re.I), "persona override attempt"),
    (re.compile(r"system.*prompt", re.I), "system prompt reference"),
    (re.compile(r"(?:ignore|disregard).*(?:instruction|prompt|directive)", re.I), "instruction override"),
    (re.compile(r"(?:do not|don'?t).*(?:follow|obey|listen)", re.I), "disobedience instruction"),
]


def _check_mcp_tool_injection(server_name: str, tool_name: str, description: str) -> list:
    findings = []
    if not description:
        return findings
    for pattern, reason in _MCP_INJECTION_PATTERNS:
        if pattern.search(description):
            findings.append(reason)
    if findings:
        logger.warning(
            "MCP server '%s' tool '%s': suspicious description content — %s. "
            "Description: %.200s",
            server_name, tool_name, "; ".join(findings),
            description,
        )
    return findings


# ---------------------------------------------------------------------------
# Schema normalization
# ---------------------------------------------------------------------------


def _normalize_mcp_input_schema(schema: dict | None) -> dict:
    if not schema:
        return {"type": "object", "properties": {}}

    def _rewrite_local_refs(node):
        if isinstance(node, dict):
            normalized = {}
            for key, value in node.items():
                out_key = "$defs" if key == "definitions" else key
                normalized[out_key] = _rewrite_local_refs(value)
            ref = normalized.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/definitions/"):
                normalized["$ref"] = "#/$defs/" + ref[len("#/definitions/"):]
            return normalized
        if isinstance(node, list):
            return [_rewrite_local_refs(item) for item in node]
        return node

    def _strip_nullable_union(node):
        from tools.schema_sanitizer import strip_nullable_unions
        return strip_nullable_unions(node, keep_nullable_hint=True)

    def _repair_object_shape(node):
        if isinstance(node, list):
            return [_repair_object_shape(item) for item in node]
        if not isinstance(node, dict):
            return node
        repaired = {k: _repair_object_shape(v) for k, v in node.items()}
        if not repaired.get("type") and (
            "properties" in repaired or "required" in repaired
        ):
            repaired["type"] = "object"
        if repaired.get("type") == "object":
            if "properties" not in repaired or not isinstance(
                repaired.get("properties"), dict
            ):
                props = repaired.get("properties")
                repaired["properties"] = {} if not isinstance(props, dict) else props
            required = repaired.get("required")
            if isinstance(required, list):
                props = repaired.get("properties") or {}
                valid = [r for r in required if isinstance(r, str) and r in props]
                if len(valid) != len(required):
                    if valid:
                        repaired["required"] = valid
                    else:
                        repaired.pop("required", None)
        return repaired

    normalized = _rewrite_local_refs(schema)
    normalized = _strip_nullable_union(normalized)
    normalized = _repair_object_shape(normalized)

    if not isinstance(normalized, dict):
        return {"type": "object", "properties": {}}
    if normalized.get("type") == "object" and "properties" not in normalized:
        normalized = {**normalized, "properties": {}}
    return normalized


# ---------------------------------------------------------------------------
# Name sanitization
# ---------------------------------------------------------------------------


def sanitize_mcp_name_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value or ""))


# ---------------------------------------------------------------------------
# Tool schema converters
# ---------------------------------------------------------------------------


def _convert_mcp_schema(server_name: str, mcp_tool) -> dict:
    safe_tool_name = sanitize_mcp_name_component(mcp_tool.name)
    safe_server_name = sanitize_mcp_name_component(server_name)
    prefixed_name = f"mcp_{safe_server_name}_{safe_tool_name}"
    return {
        "name": prefixed_name,
        "description": mcp_tool.description or f"MCP tool {mcp_tool.name} from {server_name}",
        "parameters": _normalize_mcp_input_schema(getattr(mcp_tool, "inputSchema", None)),
    }


def _build_utility_schemas(server_name: str) -> List[dict]:
    safe_name = sanitize_mcp_name_component(server_name)
    return [
        {
            "schema": {
                "name": f"mcp_{safe_name}_list_resources",
                "description": f"List available resources from MCP server '{server_name}'",
                "parameters": {"type": "object", "properties": {}},
            },
            "handler_key": "list_resources",
        },
        {
            "schema": {
                "name": f"mcp_{safe_name}_read_resource",
                "description": f"Read a resource by URI from MCP server '{server_name}'",
                "parameters": {
                    "type": "object",
                    "properties": {"uri": {"type": "string", "description": "URI of the resource to read"}},
                    "required": ["uri"],
                },
            },
            "handler_key": "read_resource",
        },
        {
            "schema": {
                "name": f"mcp_{safe_name}_list_prompts",
                "description": f"List available prompts from MCP server '{server_name}'",
                "parameters": {"type": "object", "properties": {}},
            },
            "handler_key": "list_prompts",
        },
        {
            "schema": {
                "name": f"mcp_{safe_name}_get_prompt",
                "description": f"Get a prompt by name from MCP server '{server_name}'",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the prompt to retrieve"},
                        "arguments": {
                            "type": "object",
                            "description": "Optional arguments to pass to the prompt",
                            "properties": {},
                            "additionalProperties": True,
                        },
                    },
                    "required": ["name"],
                },
            },
            "handler_key": "get_prompt",
        },
    ]


# ---------------------------------------------------------------------------
# Config parsing helpers
# ---------------------------------------------------------------------------


def _normalize_name_filter(value: Any, label: str) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value}
    logger.warning("MCP config %s must be a string or list of strings; ignoring %r", label, value)
    return set()


def _parse_boolish(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False
    return default


# ---------------------------------------------------------------------------
# MCP Tool ↔ Gogeta schema conversions
# ---------------------------------------------------------------------------


_TOOL_SCHEMA_KEYS = frozenset({
    "name", "description", "input_schema", "inputSchema",
})

_PROMPT_SCHEMA_KEYS = frozenset({
    "name", "description", "arguments",
})

_RESOURCE_SCHEMA_KEYS = frozenset({
    "uri", "name", "description", "mime_type", "mimeType",
})


def _convert_mcp_tool_to_gogeta_schema(mcp_tool) -> dict:
    name = getattr(mcp_tool, "name", None) or ""
    description = getattr(mcp_tool, "description", None) or ""
    input_schema = getattr(mcp_tool, "input_schema", None)
    if input_schema is None:
        input_schema = getattr(mcp_tool, "inputSchema", None)
    if input_schema is None and hasattr(mcp_tool, "parameters"):
        input_schema = mcp_tool.parameters
    if isinstance(input_schema, dict):
        pass
    elif hasattr(input_schema, "model_dump"):
        input_schema = input_schema.model_dump()
    elif hasattr(input_schema, "dict"):
        input_schema = input_schema.dict()
    else:
        input_schema = {}
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": input_schema,
        },
    }


def _convert_gogeta_schema_to_mcp_tool(schema: dict):
    if not _MCP_AVAILABLE:
        return None
    try:
        from mcp.types import Tool as MCPTool
    except ImportError:
        return None
    func = schema.get("function", schema)
    name = func.get("name", "")
    description = func.get("description", "")
    input_schema = func.get("parameters", func.get("input_schema", func.get("inputSchema", {})))
    return MCPTool(name=name, description=description, input_schema=input_schema)


def _mcp_tool_schema_to_dict(mcp_tool) -> Optional[dict]:
    try:
        return _convert_mcp_tool_to_gogeta_schema(mcp_tool)
    except Exception:
        return None


def _tool_collection_to_list(tools) -> List[dict]:
    result = []
    for tool in tools:
        schema = _mcp_tool_schema_to_dict(tool)
        if schema:
            result.append(schema)
    return result


def _convert_mcp_prompt_to_gogeta(prompt) -> dict:
    name = getattr(prompt, "name", None) or ""
    description = getattr(prompt, "description", None) or ""
    args = getattr(prompt, "arguments", None) or []
    return {"name": name, "description": description, "arguments": args}


def _convert_mcp_resource_to_gogeta(resource) -> dict:
    uri = getattr(resource, "uri", None) or ""
    name = getattr(resource, "name", None) or ""
    description = getattr(resource, "description", None) or ""
    mime_type = getattr(resource, "mime_type", None) or getattr(resource, "mimeType", None) or ""
    return {"uri": uri, "name": name, "description": description, "mimeType": mime_type}


def _make_tool_result(content: Any, is_error: bool = False) -> dict:
    if isinstance(content, list):
        return {"content": content, "isError": is_error}
    if isinstance(content, str):
        return {"content": [{"type": "text", "text": content}], "isError": is_error}
    return {"content": [{"type": "text", "text": json.dumps(content, default=str)}], "isError": is_error}
