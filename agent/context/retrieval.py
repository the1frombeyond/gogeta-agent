"""Context retrieval — fetches relevant knowledge from Lifeline, Genome, and
Project Intelligence for injection into the context window.

This is the bridge that connects the context engine to Gogeta's identity
(Lifeline) and learning (Genome) systems.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ranking import RelevanceRanker

logger = logging.getLogger(__name__)

_LIFELINE_DIR = Path("gogeta") / "lifeline"
_GENOME_DIR = Path("gogeta") / "genome"
_PROJECT_DIR = Path.cwd()


class ContextRetrieval:
    """Retrieves relevant context items from Gogeta's knowledge systems.

    Usage::

        retrieval = ContextRetrieval()
        memories = retrieval.get_relevant_memories(keywords=["bug", "fix"])
        workflows = retrieval.get_relevant_workflows(keywords=["test"])
        context = retrieval.get_all_relevant(keywords=["python", "refactor"])
    """

    def __init__(
        self,
        lifeline_dir: Optional[Path] = None,
        genome_dir: Optional[Path] = None,
    ):
        self._lifeline_dir = lifeline_dir or _LIFELINE_DIR
        self._genome_dir = genome_dir or _GENOME_DIR
        self._ranker = RelevanceRanker()

    # ── Lifeline retrieval ──────────────────────────────────────────

    def get_memories(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """Read memories from lifeline MEMORIES.md."""
        path = self._lifeline_dir / "MEMORIES.md"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        result = []
        current_cat = "general"
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                current_cat = stripped[3:]
            elif stripped.startswith("- ") and (category is None or current_cat == category):
                result.append({"category": current_cat, "fact": stripped[2:]})
        return result

    def get_failures(self, limit: int = 5) -> List[Dict[str, str]]:
        """Read recent failures from FAILURES.md."""
        path = self._lifeline_dir / "FAILURES.md"
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
                current = {"date": parts[0] if len(parts) > 1 else "", "attempt": parts[-1] if parts else ""}
            elif stripped.startswith("**Problem:**"):
                current["problem"] = stripped[len("**Problem:** "):]
            elif stripped.startswith("**Lesson:**"):
                current["lesson"] = stripped[len("**Lesson:** "):]
        if current:
            failures.append(current)
        return failures[-limit:]

    def get_decisions(self, limit: int = 5) -> List[Dict[str, str]]:
        """Read recent decisions from DECISIONS.md."""
        path = self._lifeline_dir / "DECISIONS.md"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        decisions = []
        current: Dict = {}
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                if current:
                    decisions.append(current)
                parts = stripped[3:].split(": ", 1)
                current = {"date": parts[0] if len(parts) > 1 else "", "decision": parts[-1] if parts else ""}
            elif stripped.startswith("**Reason:**"):
                current["reason"] = stripped[len("**Reason:** "):]
            elif stripped.startswith("**Alternatives:**"):
                current["alternatives"] = stripped[len("**Alternatives:** "):]
        if current:
            decisions.append(current)
        return decisions[-limit:]

    # ── Genome retrieval ────────────────────────────────────────────

    def get_workflows(self) -> List[Dict]:
        """Read genome workflows."""
        from gogeta.genome.storage import GenomeStorage
        try:
            storage = GenomeStorage(self._genome_dir)
            return storage.load_workflows()
        except Exception as exc:
            logger.debug("Genome workflow retrieval failed: %s", exc)
            return []

    def get_rules(self) -> List[Dict]:
        """Read genome rules."""
        from gogeta.genome.storage import GenomeStorage
        try:
            storage = GenomeStorage(self._genome_dir)
            return storage.load_rules()
        except Exception as exc:
            logger.debug("Genome rule retrieval failed: %s", exc)
            return []

    def get_skills(self) -> List[Dict]:
        """Read genome skills."""
        from gogeta.genome.storage import GenomeStorage
        try:
            storage = GenomeStorage(self._genome_dir)
            return storage.load_skills()
        except Exception as exc:
            logger.debug("Genome skill retrieval failed: %s", exc)
            return []

    # ── Project intelligence retrieval ──────────────────────────────

    def get_project_md(self) -> str:
        """Read project.md if it exists."""
        path = _PROJECT_DIR / "project.md"
        if path.exists():
            return path.read_text(encoding="utf-8")[:2000]
        return ""

    def get_tasks_md(self) -> str:
        """Read tasks.md if it exists."""
        path = _PROJECT_DIR / "tasks.md"
        if path.exists():
            return path.read_text(encoding="utf-8")[:2000]
        return ""

    def get_decision_log(self) -> str:
        """Read decision_log.md if it exists."""
        path = _PROJECT_DIR / "decision_log.md"
        if path.exists():
            return path.read_text(encoding="utf-8")[:2000]
        return ""

    # ── Combined relevance search ───────────────────────────────────

    def get_relevant_memories(
        self,
        keywords: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """Return top-k memories relevant to keywords."""
        all_memories = self.get_memories()
        return self._ranker.filter_top(
            all_memories, self._ranker.score_memory,
            keywords=keywords, top_k=top_k, min_score=0.1,
        )

    def get_relevant_workflows(
        self,
        keywords: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> List[Dict]:
        """Return top-k genome workflows relevant to keywords."""
        workflows = self.get_workflows()
        return self._ranker.filter_top(
            workflows, self._ranker.score_workflow,
            keywords=keywords, top_k=top_k, min_score=0.1,
        )

    def get_relevant_rules(
        self,
        keywords: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> List[Dict]:
        """Return top-k genome rules relevant to keywords."""
        rules = self.get_rules()
        return self._ranker.filter_top(
            rules, self._ranker.score_rule,
            keywords=keywords, top_k=top_k, min_score=0.1,
        )

    def get_all_relevant(
        self,
        keywords: Optional[List[str]] = None,
        max_memories: int = 5,
        max_workflows: int = 3,
        max_rules: int = 3,
    ) -> Dict[str, Any]:
        """Return all relevant context from all sources in one call."""
        return {
            "memories": self.get_relevant_memories(keywords, max_memories),
            "workflows": self.get_relevant_workflows(keywords, max_workflows),
            "rules": self.get_relevant_rules(keywords, max_rules),
            "failures": self.get_failures(limit=3),
            "decisions": self.get_decisions(limit=3),
        }
