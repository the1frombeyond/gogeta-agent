"""Failure learning — reads FAILURES.md and extracts reusable rules.

Converts raw failure entries into genome rules that prevent repeat mistakes.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from .storage import GenomeStorage

logger = logging.getLogger(__name__)

_FAILURES_PATH = Path("gogeta") / "lifeline" / "FAILURES.md"


def learn_from_failures(
    storage: GenomeStorage,
    failures_path: Optional[Path] = None,
) -> List[Dict]:
    """Parse FAILURES.md and extract rules into the genome.

    Each failure entry becomes a rule if the lesson is non-trivial.
    """
    if failures_path is None:
        failures_path = Path.cwd() / _FAILURES_PATH
    if not failures_path.exists():
        return []

    text = failures_path.read_text(encoding="utf-8")
    entries = _parse_failures(text)

    new_rules: List[Dict] = []
    for entry in entries:
        lesson = entry.get("lesson", "").strip()
        problem = entry.get("problem", "").strip()
        attempt = entry.get("attempt", "").strip()
        date = entry.get("date", "unknown")

        if not lesson or len(lesson) < 10:
            continue

        rule_text = _lesson_to_rule(lesson, problem, attempt)
        rule = {
            "rule": rule_text,
            "source": "failure",
            "date": date,
            "lesson": lesson,
            "problem": problem,
            "attempt": attempt[:60],
        }
        storage.add_rule(rule)
        new_rules.append(rule)
        storage.add_evolution_entry({
            "action": "rule_learned",
            "rule": rule_text[:80],
            "source": "failure",
        })
        logger.info("Genome learned rule from failure: %s", rule_text[:80])

    return new_rules


def _parse_failures(text: str) -> List[Dict]:
    """Parse the lifeline FAILURES.md format."""
    entries: List[Dict] = []
    current: Dict = {}
    date_pattern = re.compile(r"^## (\d{4}-\d{2}-\d{2}): (.+)$")

    for line in text.splitlines():
        stripped = line.strip()
        m = date_pattern.match(stripped)
        if m:
            if current:
                entries.append(current)
            current = {"date": m.group(1), "attempt": m.group(2)}
        elif stripped.startswith("**Problem:**"):
            current["problem"] = stripped[len("**Problem:** "):]
        elif stripped.startswith("**Solution:**"):
            current["solution"] = stripped[len("**Solution:** "):]
        elif stripped.startswith("**Lesson:**"):
            current["lesson"] = stripped[len("**Lesson:** "):]
    if current:
        entries.append(current)
    return entries


def _lesson_to_rule(lesson: str, problem: str, attempt: str) -> str:
    """Convert a lesson into a generalised rule."""
    # Patterns that map to common rules
    lesson_lower = lesson.lower()
    problem_lower = problem.lower()

    if "expir" in lesson_lower or "refresh" in lesson_lower:
        return "Authentication tokens must be persisted and refreshed before expiry."
    if "import" in lesson_lower or "import error" in problem_lower:
        return "Always verify imports before using a module."
    if "generated" in lesson_lower or "generated" in problem_lower:
        return "Generated files are read-only — never modify them directly."
    if "test" in lesson_lower and ("break" in problem_lower or "fail" in problem_lower):
        return "Run tests before and after every change to catch regressions."
    if "circular" in problem_lower:
        return "Avoid circular dependencies — use dependency inversion or events."
    if "not found" in problem_lower or "missing" in problem_lower:
        return "Verify file existence before reading or editing."
    if "permission" in problem_lower or "denied" in problem_lower:
        return "Check file permissions before write operations."

    return f"{lesson.strip('.')}."
