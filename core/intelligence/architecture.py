"""Architecture documentation manager — maintains ``architecture.md``.

Tracks components, their relationships, and data flow. Updated when the
Project Intelligence subscriber detects component-level changes.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ArchitectureManager:
    """Records component definitions and their relationships.

    Each component has a name, description, dependencies (components it
    depends on), and dependents (components that depend on it).
    """

    def __init__(self, path: Optional[Path] = None):
        if path is None:
            path = Path.cwd() / "architecture.md"
        self._path = path
        self._components: Dict[str, dict] = {}
        self._load()

    @property
    def path(self) -> Path:
        return self._path

    def register_component(self, name: str, description: str = "") -> None:
        if name not in self._components:
            self._components[name] = {
                "name": name,
                "description": description,
                "dependencies": [],
                "dependents": [],
            }
            self._save()

    def add_dependency(self, component: str, depends_on: str) -> None:
        self.register_component(component)
        self.register_component(depends_on)
        if depends_on not in self._components[component]["dependencies"]:
            self._components[component]["dependencies"].append(depends_on)
        if component not in self._components[depends_on]["dependents"]:
            self._components[depends_on]["dependents"].append(component)
        self._save()

    def list_components(self) -> List[str]:
        return sorted(self._components.keys())

    def get_component(self, name: str) -> Optional[dict]:
        return self._components.get(name)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError:
            return
        current = None
        in_deps = False
        in_dependents = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                name = stripped[3:]
                self._components[name] = {
                    "name": name, "description": "",
                    "dependencies": [], "dependents": [],
                }
                current = name
                in_deps = False
                in_dependents = False
            elif current and stripped.startswith("**"):
                in_deps = "dependencies" in stripped.lower()
                in_dependents = "dependents" in stripped.lower()
            elif current and stripped.startswith("- ") and in_deps:
                dep = stripped[2:]
                if dep not in self._components[current]["dependencies"]:
                    self._components[current]["dependencies"].append(dep)
            elif current and stripped.startswith("- ") and in_dependents:
                dep = stripped[2:]
                if dep not in self._components[current]["dependents"]:
                    self._components[current]["dependents"].append(dep)

    def _save(self) -> None:
        lines = ["# Architecture\n"]
        for name in sorted(self._components.keys()):
            comp = self._components[name]
            lines.append(f"## {name}")
            if comp["description"]:
                lines.append(f"\n{comp['description']}\n")
            if comp["dependencies"]:
                lines.append("**Dependencies:**")
                for dep in comp["dependencies"]:
                    lines.append(f"- {dep}")
                lines.append("")
            if comp["dependents"]:
                lines.append("**Used By:**")
                for dep in comp["dependents"]:
                    lines.append(f"- {dep}")
                lines.append("")
        try:
            self._path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to write %s: %s", self._path, exc)
