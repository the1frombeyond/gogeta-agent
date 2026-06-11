"""Project state manager — maintains ``project.md`` from events.

Tracks the current goal, status, active work, completed items, modified
files, and next steps. Updated automatically by the Project Intelligence
subscriber whenever relevant events fire.
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_SECTION_ORDER = [
    "goal", "status", "active_work", "completed", "files_modified",
    "tests", "issues", "next_steps",
]


class ProjectManager:
    """Reads and writes ``project.md`` in a target directory.

    The file is a flat markdown doc with named sections. Only sections
    that have been explicitly set are written.
    """

    SECTION_HEADERS = {
        "goal": "Goal",
        "status": "Status",
        "active_work": "Active Work",
        "completed": "Completed",
        "files_modified": "Files Modified",
        "dependencies": "Dependencies Added",
        "tests": "Tests",
        "issues": "Issues",
        "next_steps": "Next Steps",
    }

    def __init__(self, path: Optional[Path] = None):
        if path is None:
            path = Path.cwd() / "project.md"
        self._path = path
        self._data: Dict[str, List[str]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._path

    def set(self, section: str, value: str) -> None:
        if section not in self.SECTION_HEADERS:
            logger.debug("Unknown project section '%s' — writing anyway", section)
        self._data.setdefault(section, []).append(value)
        self._save()

    def set_list(self, section: str, items: List[str]) -> None:
        if section not in self.SECTION_HEADERS:
            logger.debug("Unknown project section '%s' — writing anyway", section)
        self._data[section] = items
        self._save()

    def add(self, section: str, item: str) -> None:
        if section not in self.SECTION_HEADERS:
            logger.debug("Unknown project section '%s' — writing anyway", section)
        self._data.setdefault(section, []).append(item)
        self._save()

    def append_to(self, section: str, item: str) -> None:
        """Append a single item to a list section (e.g. files_modified)."""
        self._data.setdefault(section, [])
        if item not in self._data[section]:
            self._data[section].append(item)
            self._save()

    def clear_section(self, section: str) -> None:
        self._data.pop(section, None)
        self._save()

    def get(self, section: str, default: str = "") -> str:
        items = self._data.get(section, [])
        return items[-1] if items else default

    def snapshot(self) -> Dict[str, List[str]]:
        return dict(self._data)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError:
            return
        current_section = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                current_section = None
                continue
            header = self._header_for_value(stripped)
            if header:
                current_section = header
                self._data.setdefault(current_section, [])
                continue
            if current_section and stripped.startswith("- "):
                self._data.setdefault(current_section, []).append(stripped[2:])

    def _save(self) -> None:
        lines = ["# Project State", ""]
        for section in _SECTION_ORDER:
            items = self._data.get(section)
            if not items:
                continue
            header = self.SECTION_HEADERS.get(section, section.replace("_", " ").title())
            lines.append(f"**{header}:**")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
        try:
            self._path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to write %s: %s", self._path, exc)

    def _header_for_value(self, line: str) -> Optional[str]:
        for key, header in self.SECTION_HEADERS.items():
            if line == f"**{header}:**":
                return key
        return None
