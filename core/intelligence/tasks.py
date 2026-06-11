"""Task tracker — maintains ``tasks.md``.

Tracks what's been done and what's left. Auto-updated by the Project
Intelligence subscriber when tool events suggest task progress.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class TaskManager:
    """Simple markdown task list with In Progress / Completed sections."""

    def __init__(self, path: Optional[Path] = None):
        if path is None:
            path = Path.cwd() / "tasks.md"
        self._path = path
        self._in_progress: List[str] = []
        self._completed: List[str] = []
        self._load()

    @property
    def path(self) -> Path:
        return self._path

    def add(self, description: str) -> None:
        self._in_progress.append(description)
        self._save()

    def complete(self, description: str) -> None:
        if description in self._in_progress:
            self._in_progress.remove(description)
        date = datetime.now().strftime("%Y-%m-%d")
        self._completed.append(f"{description} ({date})")
        self._save()

    def complete_current(self) -> None:
        """Mark the most recent in-progress task as done."""
        if self._in_progress:
            self.complete(self._in_progress[0])

    def list_in_progress(self) -> List[str]:
        return list(self._in_progress)

    def list_completed(self) -> List[str]:
        return list(self._completed)

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
            if stripped.startswith("## "):
                current_section = stripped[3:].lower()
                continue
            if stripped.startswith("- [ ] ") and current_section == "in progress":
                self._in_progress.append(stripped[6:])
            elif stripped.startswith("- [x] ") and current_section == "completed":
                self._completed.append(stripped[6:])

    def _save(self) -> None:
        lines = ["# Tasks\n"]
        if self._in_progress:
            lines.append("## In Progress\n")
            for task in self._in_progress:
                lines.append(f"- [ ] {task}")
            lines.append("")
        if self._completed:
            lines.append("## Completed\n")
            for task in self._completed:
                lines.append(f"- [x] {task}")
            lines.append("")
        try:
            self._path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to write %s: %s", self._path, exc)
