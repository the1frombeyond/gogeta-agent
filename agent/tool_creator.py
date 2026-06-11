"""Autonomous Tool Creator — Law 4 of the Gogeta Autonomy Directive.

Detects missing functionality, generates tool code, registers it in the
tool registry, wires it into a toolset, tests it, and documents it.

The cycle:
  1. DETECT — identify gaps via explicit request or conversation analysis
  2. GENERATE — LLM produces valid Python tool code matching the repo pattern
  3. REGISTER — write file to tools/, registry.register(), wire into toolset
  4. TEST — execute with sample input to verify
  5. DOCUMENT — record the new tool in the genome for future reference
"""

from __future__ import annotations

import importlib
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.events.bus import event_bus
from core.events.events import Event, EventType

logger = logging.getLogger(__name__)

TOOL_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "tools"

CREATE_TOOL_SYSTEM_PROMPT = """You are a tool creator for the Gogeta agent system.
Generate a complete Python file for a new tool following these rules:

1. File must be a single Python file with no external dependencies beyond stdlib + what's already imported in tools/*.py
2. The handler function MUST return a JSON string (json.dumps(...))
3. Use the exact registration pattern:
   ```python
   from tools.registry import registry
   registry.register(
       name="tool_name",
       toolset="user_created",
       schema={...},
       handler=lambda args, **kw: function_name(...),
       check_fn=lambda: True,
       category="user_created",
   )
   ```
4. The schema must be OpenAI-format with "name", "description", "parameters" containing "type", "properties", "required"
5. All parameters should have clear descriptions
6. Include proper error handling with try/except blocks
7. Use typing hints (Dict, List, Optional, Any from typing)
8. Log with logger = logging.getLogger(__name__)
9. The schema description must be <= 80 chars

Return ONLY valid Python code. No markdown fences, no explanations."""


class ToolCreatorEngine:
    """Autonomous tool creation engine.

    Generates, registers, tests, and wires new tools into the live system
    without requiring manual file edits or restarts.
    """

    def __init__(
        self,
        call_llm: Optional[Callable] = None,
        tools_dir: Optional[Path] = None,
    ):
        self._call_llm = call_llm
        self._tools_dir = tools_dir or TOOL_TEMPLATE_PATH
        self._created_tools: List[Dict[str, Any]] = []

    # ── Public API ───────────────────────────────────────────────────

    def create_tool(
        self,
        description: str,
        tool_name: str,
        toolset: str = "user_created",
        auto_register: bool = True,
        auto_test: bool = True,
    ) -> Dict[str, Any]:
        """Full create cycle: generate → register → test → document.

        Args:
            description: What the tool should do (natural language).
            tool_name: Unique name for the tool (snake_case).
            toolset: Which toolset to add the tool to.
            auto_register: Whether to register and wire immediately.
            auto_test: Whether to test after registration.

        Returns:
            Dict with success, tool_name, file_path, test_result, error.
        """
        result: Dict[str, Any] = {
            "success": False,
            "tool_name": tool_name,
            "file_path": "",
            "test_result": None,
            "error": None,
        }

        try:
            code = self._generate_code(description, tool_name, toolset)
            if not code:
                result["error"] = "Code generation returned empty"
                return result

            file_path = self._write_tool_file(tool_name, code)
            result["file_path"] = str(file_path)

            if auto_register:
                reg_result = self._register_tool(tool_name)
                if not reg_result["success"]:
                    result["error"] = reg_result["error"]
                    result["success"] = False
                    return result

                wire_result = self._wire_to_toolset(tool_name, toolset)
                if not wire_result["success"]:
                    logger.warning("Toolset wiring issue: %s", wire_result.get("error"))

            if auto_test:
                test_result = self._test_tool(tool_name)
                result["test_result"] = test_result
                if not test_result.get("success", False):
                    result["error"] = test_result.get("error", "Test failed")
                    result["success"] = False
                    return result

            self._document_tool(tool_name, description, toolset, code)
            self._created_tools.append({
                "tool_name": tool_name,
                "toolset": toolset,
                "description": description,
                "created_at": time.time(),
            })

            self._emit_created(tool_name, toolset)
            result["success"] = True

        except Exception as exc:
            logger.exception("Tool creation failed for '%s'", tool_name)
            result["error"] = str(exc)

        return result

    def detect_missing_capabilities(
        self,
        conversation_context: str,
    ) -> List[Dict[str, str]]:
        """Analyze conversation for missing capabilities.

        Uses LLM to identify patterns like "I wish I had a tool for X",
        repeated manual workarounds, or explicit requests for new tools.
        """
        if not self._call_llm:
            return []

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Analyze the following conversation context for missing "
                        "capabilities — things the user asked for that don't have "
                        "a dedicated tool. Return a JSON list of objects with:\n"
                        '  - "capability": short name for the missing capability\n'
                        '  - "description": what the tool should do\n'
                        '  - "confidence": 0.0 to 1.0\n'
                        '  - "evidence": the relevant text from the conversation\n\n'
                        'Only include items with confidence > 0.6. Return [] if nothing found.'
                    ),
                },
                {"role": "user", "content": conversation_context},
            ]

            response = self._call_llm(
                task="tool_detection",
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
            )

            raw = response.choices[0].message.content or "[]"
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"```\w*\n?", "", raw).strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

            return json.loads(raw) or []

        except Exception as exc:
            logger.debug("Capability detection failed: %s", exc)
            return []

    # ── Step 1: Generate ────────────────────────────────────────────

    def _generate_code(
        self,
        description: str,
        tool_name: str,
        toolset: str,
    ) -> Optional[str]:
        """Use LLM to generate tool Python code."""
        if not self._call_llm:
            logger.warning("No call_llm provided — cannot generate tool code")
            return self._generate_fallback_stub(tool_name, description, toolset)

        existing_tools = self._list_existing_tool_names()

        messages = [
            {"role": "system", "content": CREATE_TOOL_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Create a tool named '{tool_name}' in toolset '{toolset}'.\n"
                    f"Description: {description}\n\n"
                    f"Existing tool names (do NOT duplicate): {', '.join(existing_tools)}\n\n"
                    f"Rules:\n"
                    f"- Handler function must be named '{tool_name}_handler'\n"
                    f"- Return json.dumps({{'success': True, 'result': ...}})\n"
                    f"- Use `from tools.registry import registry` for registration\n"
                    f"- check_fn=lambda: True (always available)\n"
                    f"- Schema description <= 80 chars\n"
                    f"- Include logging\n"
                ),
            },
        ]

        response = self._call_llm(
            task="tool_creation",
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
        )

        raw = response.choices[0].message.content or ""

        raw = re.sub(r"^```python\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        if not raw or "registry.register" not in raw:
            logger.warning("LLM output missing registry.register, using fallback stub")
            return self._generate_fallback_stub(tool_name, description, toolset)

        return raw

    def _generate_fallback_stub(
        self,
        tool_name: str,
        description: str,
        toolset: str,
    ) -> str:
        """Generate a minimal but functional tool stub."""
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", tool_name)
        safe_desc = description.replace('"', "'")[:80]
        return f'''"""Tool: {safe_name} — {safe_desc}"""
import json
import logging
from tools.registry import registry

logger = logging.getLogger(__name__)

_SCHEMA = {{
    "name": "{safe_name}",
    "description": "{safe_desc}",
    "parameters": {{
        "type": "object",
        "properties": {{
            "input": {{
                "type": "string",
                "description": "Input for the tool",
            }},
        }},
        "required": ["input"],
    }},
}}


def {safe_name}_handler(input: str = "") -> str:
    try:
        return json.dumps({{"success": True, "result": f"Processed: {{input}}"}})
    except Exception as exc:
        return json.dumps({{"success": False, "error": str(exc)}})


def check_fn() -> bool:
    return True


registry.register(
    name="{safe_name}",
    toolset="{toolset}",
    schema=_SCHEMA,
    handler=lambda args, **kw: {safe_name}_handler(
        input=args.get("input", ""),
    ),
    check_fn=check_fn,
    category="user_created",
)
'''

    @staticmethod
    def _list_existing_tool_names() -> List[str]:
        """Get registered tool names to avoid duplicates."""
        try:
            from tools.registry import registry
            return registry.get_all_tool_names()
        except Exception:
            return []

    # ── Step 2: Register ────────────────────────────────────────────

    def _write_tool_file(self, tool_name: str, code: str) -> Path:
        """Write the generated tool code to tools/<tool_name>.py."""
        file_path = self._tools_dir / f"{tool_name}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")
        logger.info("Tool file written: %s", file_path)
        return file_path

    def _register_tool(self, tool_name: str) -> Dict[str, Any]:
        """Import the tool file to trigger registry.register()."""
        try:
            mod = importlib.import_module(f"tools.{tool_name}")
            importlib.reload(mod)

            from tools.registry import registry
            entry = registry.get_entry(tool_name)
            if entry is None:
                return {"success": False, "error": "Tool not found in registry after import"}

            logger.info("Tool registered: %s (toolset=%s)", tool_name, entry.toolset)
            return {"success": True, "toolset": entry.toolset}

        except Exception as exc:
            logger.exception("Tool registration failed: %s", exc)
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _wire_to_toolset(tool_name: str, toolset: str) -> Dict[str, Any]:
        """Ensure the tool appears in the given toolset."""
        try:
            from toolsets import create_custom_toolset

            existing = None
            try:
                from toolsets import get_toolset
                existing = get_toolset(toolset)
            except Exception:
                pass

            tools_list = [tool_name]
            includes_list: List[str] = []

            if existing:
                current_tools = existing.get("tools", [])
                if tool_name not in current_tools:
                    tools_list = list(current_tools) + [tool_name]
                else:
                    tools_list = current_tools
                includes_list = existing.get("includes", [])
                description = existing.get("description", f"User-created tools in {toolset}")
            else:
                description = f"User-created tools in {toolset}"

                from toolsets import TOOLSETS
                if toolset in TOOLSETS:
                    ts = TOOLSETS[toolset]
                    tools_list = list(ts.get("tools", []))
                    if tool_name not in tools_list:
                        tools_list.append(tool_name)

            create_custom_toolset(
                name=toolset,
                description=description,
                tools=list(dict.fromkeys(tools_list)),
                includes=includes_list,
            )
            logger.info("Toolset '%s' updated with tool '%s'", toolset, tool_name)
            return {"success": True}

        except Exception as exc:
            logger.warning("Toolset wiring failed: %s", exc)
            return {"success": False, "error": str(exc)}

    # ── Step 3: Test ───────────────────────────────────────────────

    def _test_tool(self, tool_name: str) -> Dict[str, Any]:
        """Execute the tool with sample input to verify it works."""
        try:
            from tools.registry import registry

            schema = registry.get_schema(tool_name)
            if not schema:
                return {"success": False, "error": "No schema found"}

            params = schema.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])

            sample_args = {}
            for prop_name, prop_schema in properties.items():
                sample_args[prop_name] = self._generate_sample_value(
                    prop_name, prop_schema
                )

            if not sample_args and required:
                sample_args[required[0]] = "test"

            result_str = registry.dispatch(
                tool_name,
                sample_args,
                task_id="tool_creator_test",
            )

            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            if result.get("success", False):
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": result.get("error", "Handler returned success=False")}

        except Exception as exc:
            logger.exception("Tool test failed: %s", exc)
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _generate_sample_value(name: str, schema: Dict) -> Any:
        """Generate a plausible sample value for a parameter based on its schema."""
        schema_type = schema.get("type", "string")

        if schema_type == "string":
            enum = schema.get("enum")
            if enum:
                return enum[0]
            if "path" in name.lower() or "file" in name.lower():
                return "/tmp/test.txt"
            if "url" in name.lower():
                return "https://example.com"
            if "email" in name.lower():
                return "test@example.com"
            return "test_input"
        elif schema_type == "integer" or schema_type == "number":
            return 1
        elif schema_type == "boolean":
            return True
        elif schema_type == "array":
            return []
        elif schema_type == "object":
            return {}
        return None

    # ── Step 4: Document ────────────────────────────────────────────

    @staticmethod
    def _document_tool(
        tool_name: str,
        description: str,
        toolset: str,
        code: str,
    ) -> None:
        """Record the tool creation in the genome for future reference."""
        try:
            from gogeta.genome.storage import GenomeStorage
            storage = GenomeStorage()
            storage.add_evolution_entry({
                "event": "tool_created",
                "tool_name": tool_name,
                "toolset": toolset,
                "description": description,
                "timestamp": time.time(),
                "lines_of_code": len(code.strip().split("\n")),
            })
        except Exception as exc:
            logger.debug("Tool documentation failed: %s", exc)

    # ── Event emission ─────────────────────────────────────────────

    @staticmethod
    def _emit_created(tool_name: str, toolset: str) -> None:
        try:
            event_bus.emit(Event(
                type=EventType.SYSTEM_CONFIGURED,
                source="tool_creator",
                data={
                    "event": "tool_created",
                    "tool_name": tool_name,
                    "toolset": toolset,
                },
            ))
        except Exception:
            pass

    # ── Properties ─────────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_created": len(self._created_tools),
            "tools": self._created_tools,
        }
