"""Enhanced tool discovery — finds tools from multiple sources.

Extends the existing ``discover_builtin_tools()`` AST-based auto-discovery
with category-based, plugin-based, and skill-based discovery.
"""

import importlib
import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def discover_category_tools(categories_dir: Optional[Path] = None) -> List[str]:
    """Import all tool modules under ``tools/categories/``.

    Each module is expected to call ``registry.register()`` at module level.
    Returns the list of imported module names.
    """
    if categories_dir is None:
        categories_dir = Path(__file__).resolve().parent / "categories"
    if not categories_dir.is_dir():
        return []

    from tools.registry import _module_registers_tools

    imported: List[str] = []
    for module_path in sorted(categories_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue
        if not _module_registers_tools(module_path):
            continue
        mod_name = f"tools.categories.{module_path.stem}"
        try:
            importlib.import_module(mod_name)
            imported.append(mod_name)
        except Exception as exc:
            logger.warning("Could not import category tool %s: %s", mod_name, exc)
    return imported


def discover_plugin_tools(plugins_dir: Optional[Path] = None) -> List[str]:
    """Import tool modules from ``tools/plugins/``.

    Plugin modules follow the same ``registry.register()`` pattern.
    Returns the list of imported module names.
    """
    if plugins_dir is None:
        plugins_dir = Path(__file__).resolve().parent / "plugins"
    if not plugins_dir.is_dir():
        return []

    from tools.registry import _module_registers_tools

    imported: List[str] = []
    for module_path in sorted(plugins_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue
        if not _module_registers_tools(module_path):
            continue
        mod_name = f"tools.plugins.{module_path.stem}"
        try:
            importlib.import_module(mod_name)
            imported.append(mod_name)
        except Exception as exc:
            logger.warning("Could not import plugin tool %s: %s", mod_name, exc)
    return imported


def discover_skill_tools(skills_dir: Optional[Path] = None) -> Dict[str, str]:
    """Scan skills and return a mapping of ``{tool_name: skill_name}``.

    Skills that declare tool definitions in their metadata are registered
    on-the-fly.  This function only discovers what's available; registration
    is handled elsewhere.
    """
    result: Dict[str, str] = {}
    if skills_dir is None:
        try:
            from gogeta_constants import get_gogeta_home
            skills_dir = get_gogeta_home() / "skills"
        except ImportError:
            skills_dir = Path.home() / ".gogeta" / "skills"

    if not skills_dir.is_dir():
        return result

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        manifest = skill_dir / "SKILL.md"
        if not manifest.exists():
            continue
        skill_name = skill_dir.name
        try:
            text = manifest.read_text(encoding="utf-8")
            for line in text.splitlines():
                if line.startswith("tools:"):
                    tools_part = line.split(":", 1)[1].strip()
                    for t in tools_part.split(","):
                        tname = t.strip()
                        if tname:
                            result[tname] = skill_name
        except Exception as exc:
            logger.debug("Could not parse skill %s: %s", skill_name, exc)

    return result


def full_discover() -> Dict[str, List[str]]:
    """Run all discovery paths and return a summary.

    Returns::

        {
            "builtin": ["tools.file_tools", ...],
            "category": ["tools.categories.code_tools", ...],
            "plugin": ["tools.plugins.my_tool", ...],
        }
    """
    from tools.registry import discover_builtin_tools

    return {
        "builtin": discover_builtin_tools(),
        "category": discover_category_tools(),
        "plugin": discover_plugin_tools(),
    }


def discover_tools() -> List[str]:
    """Convenience: discover and import all available tools."""
    summary = full_discover()
    total = sum(len(v) for v in summary.values())
    logger.info("Discovered %d tool modules (%d builtin, %d category, %d plugin)",
                total, len(summary["builtin"]),
                len(summary["category"]), len(summary["plugin"]))
    return summary["builtin"] + summary["category"] + summary["plugin"]
