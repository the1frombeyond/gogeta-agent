"""LifelineManager — manages Gogeta's persistent identity files.

All files live under ``gogeta/lifeline/`` relative to the project root.
The manager auto-creates files on first write and provides get/set methods
for each document.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_LIFELINE_DIR = Path("gogeta") / "lifeline"


class LifelineManager:
    """Unified manager for all lifeline identity files.

    Usage::

        from gogeta.lifeline import LifelineManager
        ll = LifelineManager()
        ll.add_timeline_entry("Built Event Bus", ["core/events/bus.py"], "Success")
        ll.add_memory("User prefers event-driven architecture")
        ll.add_failure("Direct analytics", "Tight coupling", "Event Bus", "Route through events")
    """

    def __init__(self, lifeline_dir: Optional[Path] = None):
        if lifeline_dir is None:
            lifeline_dir = Path.cwd() / _LIFELINE_DIR
        self._dir = lifeline_dir
        self._reflections_dir = lifeline_dir / "REFLECTIONS"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._reflections_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # SOUL.md — core identity
    # ------------------------------------------------------------------

    SOUL_DEFAULT = """# Gogeta Identity

## Name
Gogeta

## Purpose
Build, learn, improve, assist.

## Principles
- Never destroy working code.
- Preserve user intent.
- Document decisions.
- Learn from failures.
- Improve architecture continuously.
"""

    def ensure_soul(self) -> Path:
        path = self._dir / "SOUL.md"
        if not path.exists():
            path.write_text(self.SOUL_DEFAULT.strip() + "\n", encoding="utf-8")
        return path

    def read_soul(self) -> str:
        path = self.ensure_soul()
        return path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # USER.md — user profile
    # ------------------------------------------------------------------

    def ensure_user(self) -> Path:
        path = self._dir / "USER.md"
        if not path.exists():
            path.write_text("# User Profile\n\n", encoding="utf-8")
        return path

    def set_user_preference(self, key: str, value: str) -> None:
        path = self.ensure_user()
        text = path.read_text(encoding="utf-8")
        marker = f"{key}: "
        lines = text.splitlines()
        found = False
        for i, line in enumerate(lines):
            if line.startswith(marker):
                lines[i] = f"{marker}{value}"
                found = True
                break
        if not found:
            lines.append(f"{marker}{value}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def read_user(self) -> str:
        path = self.ensure_user()
        return path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # TIMELINE.md — chronological history
    # ------------------------------------------------------------------

    def ensure_timeline(self) -> Path:
        path = self._dir / "TIMELINE.md"
        if not path.exists():
            path.write_text("# Timeline\n\n", encoding="utf-8")
        return path

    def add_timeline_entry(
        self,
        title: str,
        files: Optional[List[str]] = None,
        outcome: str = "",
        details: str = "",
    ) -> None:
        path = self.ensure_timeline()
        date = datetime.now().strftime("%Y-%m-%d")
        lines = [f"## {date}: {title}", ""]
        if files:
            lines.append("**Files:**")
            for f in files:
                lines.append(f"- {f}")
            lines.append("")
        if outcome:
            lines.append(f"**Outcome:** {outcome}")
            lines.append("")
        if details:
            lines.append(details)
            lines.append("")
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def read_timeline(self, limit: int = 20) -> List[Dict]:
        path = self._dir / "TIMELINE.md"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        entries = []
        current: Dict = {}
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                if current:
                    entries.append(current)
                current = {"title": stripped[3:], "files": [], "outcome": "", "details": ""}
            elif stripped.startswith("**Files:**"):
                pass
            elif stripped.startswith("- ") and "files" in current:
                current.setdefault("files", []).append(stripped[2:])
            elif stripped.startswith("**Outcome:**"):
                current["outcome"] = stripped[len("**Outcome:** "):]
            else:
                current["details"] = stripped
        if current:
            entries.append(current)
        return entries[-limit:]

    # ------------------------------------------------------------------
    # MEMORIES.md — important facts
    # ------------------------------------------------------------------

    def ensure_memories(self) -> Path:
        path = self._dir / "MEMORIES.md"
        if not path.exists():
            path.write_text("# Memories\n\n", encoding="utf-8")
        return path

    def add_memory(self, category: str, fact: str) -> None:
        path = self.ensure_memories()
        text = path.read_text(encoding="utf-8")
        marker = f"- {fact}"
        if marker in text:
            return
        lines = text.splitlines()
        cat_header = f"## {category}"
        cat_found = False
        for i, line in enumerate(lines):
            if line.strip() == cat_header:
                lines.insert(i + 1, marker)
                cat_found = True
                break
        if not cat_found:
            lines.append("")
            lines.append(cat_header)
            lines.append("")
            lines.append(marker)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def read_memories(self) -> List[Dict[str, str]]:
        path = self._dir / "MEMORIES.md"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        result = []
        current_cat = "general"
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                current_cat = stripped[3:]
            elif stripped.startswith("- "):
                result.append({"category": current_cat, "fact": stripped[2:]})
        return result

    # ------------------------------------------------------------------
    # WORLDSTATE.md — current project understanding
    # ------------------------------------------------------------------

    def ensure_worldstate(self) -> Path:
        path = self._dir / "WORLDSTATE.md"
        if not path.exists():
            path.write_text("# World State\n\n", encoding="utf-8")
        return path

    def update_worldstate(self, section: str, content: str) -> None:
        path = self.ensure_worldstate()
        text = path.read_text(encoding="utf-8")
        marker = f"**{section}:**"
        lines = text.splitlines()
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(marker):
                lines[i + 1] = f"- {content}"
                found = True
                break
        if not found:
            lines.append("")
            lines.append(marker)
            lines.append(f"- {content}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def read_worldstate(self) -> Dict[str, str]:
        path = self._dir / "WORLDSTATE.md"
        if not path.exists():
            return {}
        text = path.read_text(encoding="utf-8")
        state: Dict[str, str] = {}
        current_key = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("**") and stripped.endswith(":**"):
                current_key = stripped[2:-3]
            elif stripped.startswith("- ") and current_key:
                state[current_key] = stripped[2:]
        return state

    # ------------------------------------------------------------------
    # MISSIONS.md — long-term goals
    # ------------------------------------------------------------------

    def ensure_missions(self) -> Path:
        path = self._dir / "MISSIONS.md"
        if not path.exists():
            path.write_text("# Missions\n\n", encoding="utf-8")
        return path

    def add_mission(self, title: str, description: str) -> None:
        path = self.ensure_missions()
        lines = path.read_text(encoding="utf-8").splitlines()
        marker = f"## {title}"
        for line in lines:
            if line.strip() == marker:
                return
        lines.append("")
        lines.append(marker)
        lines.append("")
        lines.append(description)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def complete_mission(self, title: str) -> None:
        path = self._dir / "MISSIONS.md"
        if not path.exists():
            return
        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        in_mission = False
        header_found = False
        for line in lines:
            stripped = line.strip()
            if stripped == f"## {title}" and not header_found:
                new_lines.append(f"## ~~{title}~~ (completed)")
                header_found = True
                in_mission = True
            elif in_mission and stripped == "":
                in_mission = False
                new_lines.append(line)
            elif in_mission:
                new_lines.append(f"~~{stripped}~~")
            else:
                new_lines.append(line)
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def read_missions(self) -> List[Dict[str, str]]:
        path = self._dir / "MISSIONS.md"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        missions = []
        current = {}
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                if current:
                    missions.append(current)
                title = stripped[3:].replace("~~", "").replace("(completed)", "").strip()
                current = {"title": title, "completed": "~~" in stripped}
            elif stripped and not stripped.startswith("#"):
                if "description" not in current:
                    current["description"] = ""
                current["description"] += stripped.replace("~~", "") + " "
        if current:
            missions.append(current)
        return missions

    # ------------------------------------------------------------------
    # FAILURES.md — failure log
    # ------------------------------------------------------------------

    def ensure_failures(self) -> Path:
        path = self._dir / "FAILURES.md"
        if not path.exists():
            path.write_text("# Failures\n\n", encoding="utf-8")
        return path

    def add_failure(
        self,
        attempt: str,
        problem: str,
        solution: str,
        lesson: str,
    ) -> None:
        path = self.ensure_failures()
        date = datetime.now().strftime("%Y-%m-%d")
        entry = [
            f"## {date}: {attempt}",
            "",
            f"**Problem:** {problem}",
            f"**Solution:** {solution}",
            f"**Lesson:** {lesson}",
            "",
        ]
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(entry) + "\n")

    def read_failures(self) -> List[Dict[str, str]]:
        path = self._dir / "FAILURES.md"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        failures = []
        current: Dict = {}
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                if current:
                    failures.append(current)
                parts = stripped[3:].split(": ", 1)
                current = {
                    "date": parts[0] if len(parts) > 1 else "",
                    "attempt": parts[-1] if parts else "",
                }
            elif stripped.startswith("**Problem:**"):
                current["problem"] = stripped[len("**Problem:** "):]
            elif stripped.startswith("**Solution:**"):
                current["solution"] = stripped[len("**Solution:** "):]
            elif stripped.startswith("**Lesson:**"):
                current["lesson"] = stripped[len("**Lesson:** "):]
        if current:
            failures.append(current)
        return failures

    # ------------------------------------------------------------------
    # DECISIONS.md — architecture decisions
    # ------------------------------------------------------------------

    def ensure_decisions(self) -> Path:
        path = self._dir / "DECISIONS.md"
        if not path.exists():
            path.write_text("# Decisions\n\n", encoding="utf-8")
        return path

    def add_decision(
        self,
        decision: str,
        reason: str,
        alternatives: str = "",
    ) -> None:
        path = self.ensure_decisions()
        date = datetime.now().strftime("%Y-%m-%d")
        entry = [
            f"## {date}: {decision}",
            "",
            f"**Reason:** {reason}",
            f"**Alternatives:** {alternatives}",
            "",
        ]
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(entry) + "\n")

    # ------------------------------------------------------------------
    # REFLECTIONS/ — auto-generated reflection files
    # ------------------------------------------------------------------

    def ensure_reflections(self) -> Path:
        self._reflections_dir.mkdir(exist_ok=True)
        return self._reflections_dir

    def add_reflection(self, title: str, body: str) -> Path:
        safe_name = title.lower().replace(" ", "_").replace("/", "_")[:60]
        date = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date}_{safe_name}.md"
        path = self._reflections_dir / filename
        content = [
            f"# Reflection: {title}",
            "",
            body,
            "",
        ]
        path.write_text("\n".join(content) + "\n", encoding="utf-8")
        return path

    def list_reflections(self) -> List[Path]:
        self.ensure_reflections()
        return sorted(self._reflections_dir.glob("*.md"), reverse=True)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def directory(self) -> Path:
        return self._dir

    def all_files(self) -> Dict[str, str]:
        """Return a summary of all lifeline files and their line counts."""
        result = {}
        for path in self._dir.glob("*.md"):
            try:
                lines = len(path.read_text(encoding="utf-8").splitlines())
                result[path.name] = f"{lines} lines"
            except OSError:
                result[path.name] = "unreadable"
        reflection_count = len(self.list_reflections())
        result["REFLECTIONS/"] = f"{reflection_count} files"
        return result
