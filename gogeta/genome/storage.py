"""Storage layer for the genome — reads/writes genome.json and genome.db.

genome.json holds the learned workflows, patterns, skills, and rules in a
human-readable format that also feeds the genome.md report.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _default_genome_dir() -> Path:
    try:
        from gogeta_constants import get_gogeta_home
        return get_gogeta_home() / "gogeta" / "genome"
    except ImportError:
        return Path.cwd() / "gogeta" / "genome"


class GenomeStorage:
    """Manages genome.json (workflows/patterns/skills) and genome.db (graph)."""

    def __init__(self, genome_dir: Optional[Path] = None):
        if genome_dir is None:
            genome_dir = _default_genome_dir()
        self._dir = genome_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._json_path = self._dir / "genome.json"
        self._db_path = self._dir / "genome.db"
        self._lock = Lock()
        self._ensure_json()
        self._ensure_db()

    # ── JSON store (workflows, patterns, skills, rules) ──────────────

    def _ensure_json(self) -> None:
        if not self._json_path.exists():
            self._write_json({
                "version": 1,
                "updated_at": time.time(),
                "workflows": [],
                "patterns": [],
                "skills": [],
                "rules": [],
                "evolution_log": [],
            })

    def _read_json(self) -> Dict[str, Any]:
        with self._lock:
            try:
                return json.loads(self._json_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}

    def _write_json(self, data: Dict[str, Any]) -> None:
        with self._lock:
            data["updated_at"] = time.time()
            self._json_path.write_text(
                json.dumps(data, indent=2, default=str), encoding="utf-8",
            )

    def load_workflows(self) -> List[Dict]:
        return self._read_json().get("workflows", [])

    def save_workflows(self, workflows: List[Dict]) -> None:
        data = self._read_json()
        data["workflows"] = workflows
        self._write_json(data)

    def load_patterns(self) -> List[Dict]:
        return self._read_json().get("patterns", [])

    def save_patterns(self, patterns: List[Dict]) -> None:
        data = self._read_json()
        data["patterns"] = patterns
        self._write_json(data)

    def load_skills(self) -> List[Dict]:
        return self._read_json().get("skills", [])

    def save_skills(self, skills: List[Dict]) -> None:
        data = self._read_json()
        data["skills"] = skills
        self._write_json(data)

    def load_rules(self) -> List[Dict]:
        return self._read_json().get("rules", [])

    def add_rule(self, rule: Dict) -> None:
        data = self._read_json()
        rules = data.setdefault("rules", [])
        for r in rules:
            if r.get("rule") == rule.get("rule"):
                return
        rules.append(rule)
        self._write_json(data)

    def add_evolution_entry(self, entry: Dict) -> None:
        data = self._read_json()
        log = data.setdefault("evolution_log", [])
        entry["timestamp"] = time.time()
        log.append(entry)
        self._write_json(data)

    def get_report_data(self) -> Dict[str, Any]:
        """Return all data flattened for genome.md generation."""
        return self._read_json()

    # ── SQLite DB (workflow graph edges) ─────────────────────────────

    def _ensure_db(self) -> None:
        conn = sqlite3.connect(str(self._db_path))
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workflow_graph (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    step_order INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    UNIQUE(workflow_id, step_order)
                );
                CREATE TABLE IF NOT EXISTS workflow_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    tool_a TEXT NOT NULL,
                    tool_b TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    UNIQUE(workflow_id, tool_a, tool_b)
                );
                CREATE INDEX IF NOT EXISTS idx_wf_workflow
                    ON workflow_graph(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_we_workflow
                    ON workflow_edges(workflow_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def save_workflow_graph(self, workflow_id: str, steps: List[str]) -> None:
        conn = sqlite3.connect(str(self._db_path))
        try:
            for order, tool in enumerate(steps):
                conn.execute(
                    "INSERT OR REPLACE INTO workflow_graph "
                    "(workflow_id, step_order, tool_name) VALUES (?, ?, ?)",
                    (workflow_id, order, tool),
                )
            for i in range(len(steps) - 1):
                conn.execute(
                    "INSERT OR REPLACE INTO workflow_edges "
                    "(workflow_id, tool_a, tool_b, weight) VALUES (?, ?, ?, 1.0)",
                    (workflow_id, steps[i], steps[i + 1]),
                )
            conn.commit()
        finally:
            conn.close()

    def get_workflow_steps(self, workflow_id: str) -> List[str]:
        conn = sqlite3.connect(str(self._db_path))
        try:
            rows = conn.execute(
                "SELECT tool_name FROM workflow_graph "
                "WHERE workflow_id = ? ORDER BY step_order",
                (workflow_id,),
            ).fetchall()
            return [r[0] for r in rows]
        finally:
            conn.close()
