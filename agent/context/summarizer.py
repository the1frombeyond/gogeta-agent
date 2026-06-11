"""Anchored session summarizer — maintains SESSION_SUMMARY.md on disk.

Unlike the in-memory ``_previous_summary`` in ContextCompressor, this
persists a structured summary to ``gogeta/lifeline/SESSION_SUMMARY.md``
that survives session restarts and is updated incrementally.

The summary is always structured as:

    # Session Summary

    ## Active Task
    What we're working on right now.

    ## Completed
    What was done this session.

    ## Decisions
    Key decisions made.

    ## Files Changed
    Files modified this session.

    ## Open Questions
    Anything left unresolved.

    ## Remaining Work
    What still needs doing.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_SUMMARY_PATH = Path("gogeta") / "lifeline" / "SESSION_SUMMARY.md"

_DEFAULT_SUMMARY = """# Session Summary

## Active Task
None.

## Completed
- Session started.

## Decisions
None yet.

## Files Changed
None.

## Open Questions
None.

## Remaining Work
None.
"""


class SessionSummarizer:
    """Manages the anchored SESSION_SUMMARY.md.

    The summary is updated incrementally as the session progresses and
    persists across compression boundaries and session restarts.
    """

    def __init__(self, summary_path: Optional[Path] = None):
        if summary_path is None:
            summary_path = Path.cwd() / _SUMMARY_PATH
        self._path = summary_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self.reset()

    def reset(self) -> None:
        """Reset summary to defaults (new session)."""
        self._path.write_text(_DEFAULT_SUMMARY, encoding="utf-8")

    def read(self) -> str:
        """Return the full summary text."""
        if self._path.exists():
            return self._path.read_text(encoding="utf-8")
        return _DEFAULT_SUMMARY

    def get_section(self, section: str) -> str:
        """Return one section of the summary by name."""
        text = self.read()
        marker = f"## {section}"
        lines = text.splitlines()
        capture = False
        parts: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.startswith(marker):
                if capture:
                    break
                continue
            if stripped == marker:
                capture = True
                continue
            if capture:
                parts.append(line)
        return "\n".join(parts).strip()

    def set_section(self, section: str, content: str) -> None:
        """Replace the content of one section."""
        text = self.read()
        marker = f"## {section}"
        lines = text.splitlines()
        result: List[str] = []
        in_section = False
        section_written = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                if in_section:
                    in_section = False
                    if not section_written:
                        result.append("")
                        for c in content.strip().splitlines():
                            result.append(c)
                        result.append("")
                        section_written = True
                if stripped == marker:
                    in_section = True
                    result.append(line)
                else:
                    result.append(line)
            elif in_section:
                if not stripped and not section_written:
                    result.append(line)
                    continue
                if not section_written:
                    result.append("")
                    for c in content.strip().splitlines():
                        result.append(c)
                    result.append("")
                    section_written = True
            else:
                result.append(line)
        if in_section and not section_written:
            result.append("")
            for c in content.strip().splitlines():
                result.append(c)
        self._path.write_text("\n".join(result) + "\n", encoding="utf-8")

    def update_active_task(self, task: str) -> None:
        """Set or update the active task."""
        self.set_section("Active Task", task)

    def add_completed(self, item: str) -> None:
        """Append a completed item."""
        existing = self.get_section("Completed")
        items = [l.strip("- ") for l in existing.splitlines() if l.strip().startswith("- ")]
        if item not in items:
            items.append(item)
            lines = "\n".join(f"- {i}" for i in items)
            self.set_section("Completed", lines)

    def add_decision(self, decision: str) -> None:
        """Append a decision."""
        existing = self.get_section("Decisions")
        items = [l.strip("- ") for l in existing.splitlines() if l.strip().startswith("- ")]
        if decision not in items:
            items.append(decision)
            lines = "\n".join(f"- {i}" for i in items)
            self.set_section("Decisions", lines)

    def add_file_changed(self, filepath: str) -> None:
        """Append a changed file."""
        existing = self.get_section("Files Changed")
        items = [l.strip("- ") for l in existing.splitlines() if l.strip().startswith("- ")]
        if filepath not in items:
            items.append(filepath)
            lines = "\n".join(f"- {i}" for i in items)
            self.set_section("Files Changed", lines)

    def add_open_question(self, question: str) -> None:
        """Append an open question."""
        existing = self.get_section("Open Questions")
        items = [l.strip("- ") for l in existing.splitlines() if l.strip().startswith("- ")]
        if question not in items:
            items.append(question)
            lines = "\n".join(f"- {i}" for i in items)
            self.set_section("Open Questions", lines)

    def set_remaining_work(self, work: str) -> None:
        """Set remaining work."""
        self.set_section("Remaining Work", work)

    @property
    def path(self) -> Path:
        return self._path
