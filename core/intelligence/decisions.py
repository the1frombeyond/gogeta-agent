"""Decision log manager — maintains ``decision_log.md``.

Every significant architectural or design decision is recorded with its
context, alternatives considered, and tradeoffs. This file becomes
Gogeta's institutional memory, preventing the same debate from recurring.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DecisionLog:
    """Append-only decision log stored as markdown.

    Each entry has a date, title, decision body, context, alternatives,
    and tradeoffs — rendered as a structured subsection in
    ``decision_log.md``.
    """

    def __init__(self, path: Optional[Path] = None):
        if path is None:
            path = Path.cwd() / "decision_log.md"
        self._path = path
        self._entries: List[Dict[str, str]] = []
        self._load()

    @property
    def path(self) -> Path:
        return self._path

    def record(
        self,
        title: str,
        decision: str,
        context: str = "",
        alternatives: str = "",
        tradeoffs: str = "",
    ) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = {
            "date": now,
            "title": title,
            "decision": decision,
            "context": context,
            "alternatives": alternatives,
            "tradeoffs": tradeoffs,
        }
        self._entries.append(entry)
        self._save()

    def all_entries(self) -> List[Dict[str, str]]:
        return list(self._entries)

    def last_entry(self) -> Optional[Dict[str, str]]:
        return self._entries[-1] if self._entries else None

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError:
            return
        entry: Dict[str, str] = {}
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                if entry:
                    self._entries.append(entry)
                entry = {"title": stripped[3:]}
            elif stripped.startswith("**Date:**"):
                entry["date"] = stripped[len("**Date:** "):]
            elif stripped.startswith("**Decision:**"):
                entry["decision"] = stripped[len("**Decision:** "):]
            elif stripped.startswith("**Context:**"):
                entry["context"] = stripped[len("**Context:** "):]
            elif stripped.startswith("**Alternatives:**"):
                entry["alternatives"] = stripped[len("**Alternatives:** "):]
            elif stripped.startswith("**Tradeoffs:**"):
                entry["tradeoffs"] = stripped[len("**Tradeoffs:** "):]
        if entry:
            self._entries.append(entry)

    FIELDS = ["date", "decision", "context", "alternatives", "tradeoffs"]

    def _save(self) -> None:
        lines = ["# Decision Log\n"]
        for entry in self._entries:
            title = entry.get("title", "Untitled")
            lines.append(f"## {title}")
            for field in self.FIELDS:
                val = entry.get(field, "").strip()
                if val:
                    label = field.replace("_", " ").title()
                    lines.append(f"**{label}:** {val}")
            lines.append("")
        try:
            self._path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to write %s: %s", self._path, exc)
