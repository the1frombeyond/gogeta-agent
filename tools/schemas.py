"""Schema utilities for tool definitions.

Provides builders and validators for consistent OpenAI-format tool schemas
across the unified tool platform.
"""

import json
from typing import Any, Dict, List, Optional


def parameter(
    name: str,
    type_: str,
    description: str = "",
    required: bool = True,
    enum: Optional[List[str]] = None,
    default: Any = None,
    items: Optional[Dict] = None,
) -> Dict:
    """Build a single parameter entry for a JSON Schema parameters dict.

    Example::

        parameter("path", "string", "File path to read")
        parameter("recursive", "boolean", "Search recursively", required=False)
        parameter("tags", "array", "Filter tags", required=False,
                  items={"type": "string"})
    """
    entry: Dict = {"type": type_}
    if description:
        entry["description"] = description
    if enum:
        entry["enum"] = enum
    if default is not None:
        entry["default"] = default
    if items is not None:
        entry["items"] = items
    return entry


def build_tool_schema(
    name: str,
    description: str,
    parameters: Optional[Dict[str, Dict]] = None,
    required: Optional[List[str]] = None,
) -> Dict:
    """Build a complete OpenAI-format tool schema.

    Returns the ``{"type": "function", "function": {...}}`` envelope.

    Example::

        build_tool_schema(
            "read_file",
            "Read a file from the filesystem",
            parameters={
                "path": parameter("path", "string", "Absolute file path"),
                "encoding": parameter("encoding", "string",
                                      "File encoding", required=False,
                                      default="utf-8"),
            },
        )
    """
    function_def: Dict = {
        "name": name,
        "description": description,
    }
    if parameters:
        function_def["parameters"] = {
            "type": "object",
            "properties": parameters,
            "required": required or [
                pname for pname, pdef in parameters.items()
                if pdef.get("required", True)
            ],
        }
    return {"type": "function", "function": function_def}


def build_parameters(**params: Dict) -> Dict[str, Dict]:
    """Shorthand for building a parameters dict from keyword args.

    Each value is already a parameter dict::

        build_parameters(
            path=parameter("path", "string", "File path"),
            mode=parameter("mode", "string", "Open mode", default="r"),
        )
    """
    return params


def validate_args(schema: Dict, args: Dict) -> List[str]:
    """Validate tool arguments against a schema.

    Returns a list of error messages (empty = valid).
    """
    errors: List[str] = []
    params = schema.get("parameters", {})
    properties = params.get("properties", {})

    required = set(params.get("required", []))
    for key in required:
        if key not in args or args[key] is None:
            errors.append(f"Missing required parameter: {key}")

    for key, value in args.items():
        prop = properties.get(key)
        if not prop:
            continue
        expected_type = prop.get("type", "string")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Parameter '{key}' must be a string")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Parameter '{key}' must be a number")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Parameter '{key}' must be a boolean")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"Parameter '{key}' must be an array")
        elif expected_type == "object" and not isinstance(value, dict):
            errors.append(f"Parameter '{key}' must be an object")

        enum_values = prop.get("enum")
        if enum_values and value not in enum_values:
            errors.append(
                f"Parameter '{key}' must be one of: {', '.join(enum_values)}"
            )

    return errors


def merge_schemas(base: Dict, override: Dict) -> Dict:
    """Deep-merge an override schema into a base schema.

    Both are raw function dicts (the inner ``{"name": ..., "description": ...,
    "parameters": {...}}``, NOT the OpenAI envelope). Returns a new dict.
    """
    result = dict(base)
    for key in override:
        if key == "parameters" and key in result:
            result["parameters"] = {
                "type": "object",
                "properties": {
                    **(result["parameters"].get("properties", {})),
                    **(override["parameters"].get("properties", {})),
                },
                "required": list(set(
                    result["parameters"].get("required", [])
                    + override["parameters"].get("required", [])
                )),
            }
        else:
            result[key] = override[key]
    return result
