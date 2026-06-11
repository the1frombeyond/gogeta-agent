"""Tool usage analytics — SQLite-backed store for per-call telemetry.

Every ``execute_tool()`` call records: tool name, category, session,
agent, duration, success/failure, token counts, and cost.
Data lives in ``analytics/tools.db`` relative to GOGETA_HOME.
"""

import json
import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """One recorded tool call."""

    tool_name: str = ""
    category: str = ""
    session_id: str = ""
    agent_id: str = ""
    provider: str = ""
    duration_ms: float = 0.0
    success: bool = True
    error: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    cost: float = 0.0
    timestamp: float = 0.0
    metadata: Dict = field(default_factory=dict)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    category TEXT DEFAULT '',
    session_id TEXT DEFAULT '',
    agent_id TEXT DEFAULT '',
    provider TEXT DEFAULT '',
    duration_ms REAL DEFAULT 0,
    success INTEGER DEFAULT 1,
    error TEXT DEFAULT '',
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    timestamp REAL NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_name ON tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_timestamp ON tool_calls(timestamp);

CREATE TABLE IF NOT EXISTS tool_metrics (
    tool_name TEXT PRIMARY KEY,
    total_calls INTEGER DEFAULT 0,
    total_success INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    total_duration_ms REAL DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    avg_duration_ms REAL DEFAULT 0,
    last_called REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tool_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_a TEXT NOT NULL,
    tool_b TEXT NOT NULL,
    frequency INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    total_success INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    first_seen REAL DEFAULT 0,
    last_seen REAL DEFAULT 0,
    UNIQUE(tool_a, tool_b)
);

CREATE INDEX IF NOT EXISTS idx_relationships_a ON tool_relationships(tool_a);
CREATE INDEX IF NOT EXISTS idx_relationships_b ON tool_relationships(tool_b);
"""


class AnalyticsStore:
    """Thread-safe SQLite store for tool analytics."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            try:
                from gogeta_constants import get_gogeta_home
                base = get_gogeta_home() / "analytics"
            except ImportError:
                base = Path.home() / ".gogeta" / "analytics"
            base.mkdir(parents=True, exist_ok=True)
            db_path = base / "tools.db"
        self._db_path = str(db_path)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _ensure_schema(self) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.executescript(_SCHEMA)
            conn.commit()

    def record_call(self, record: ToolCallRecord) -> None:
        """Insert one tool call record and update aggregated metrics."""
        if record.timestamp == 0:
            record.timestamp = time.time()
        try:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO tool_calls
                   (tool_name, category, session_id, agent_id, provider,
                    duration_ms, success, error, tokens_input, tokens_output,
                    cost, timestamp, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.tool_name, record.category, record.session_id,
                    record.agent_id, record.provider, record.duration_ms,
                    1 if record.success else 0, record.error,
                    record.tokens_input, record.tokens_output,
                    record.cost, record.timestamp,
                    json.dumps(record.metadata),
                ),
            )
            conn.execute(
                """INSERT INTO tool_metrics
                   (tool_name, total_calls, total_success, total_failures,
                    total_duration_ms, total_cost, avg_duration_ms, last_called)
                   VALUES (?, 1, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tool_name) DO UPDATE SET
                    total_calls = total_calls + 1,
                    total_success = total_success + ?,
                    total_failures = total_failures + ?,
                    total_duration_ms = total_duration_ms + ?,
                    total_cost = total_cost + ?,
                    avg_duration_ms = total_duration_ms / total_calls,
                    last_called = ?""",
                (
                    record.tool_name,
                    1 if record.success else 0,
                    1 if not record.success else 0,
                    record.duration_ms, record.cost,
                    record.duration_ms, record.timestamp,
                    1 if record.success else 0,
                    1 if not record.success else 0,
                    record.duration_ms, record.cost, record.timestamp,
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.debug("Analytics write failed: %s", exc)

    def get_metrics(self, tool_name: str) -> Dict:
        """Return aggregated metrics for one tool."""
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM tool_metrics WHERE tool_name = ?",
                (tool_name,),
            ).fetchone()
            if row:
                return dict(row)
        except Exception as exc:
            logger.debug("Analytics read failed: %s", exc)
        return {}

    def get_top_tools(self, limit: int = 10) -> List[Dict]:
        """Return most-called tools by total calls."""
        try:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM tool_metrics ORDER BY total_calls DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.debug("Analytics top-tools query failed: %s", exc)
        return []

    def get_recent_calls(
        self, limit: int = 50, tool_name: Optional[str] = None,
    ) -> List[Dict]:
        """Return recent call records, optionally filtered by tool name."""
        try:
            conn = self._get_conn()
            if tool_name:
                rows = conn.execute(
                    "SELECT * FROM tool_calls WHERE tool_name = ? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (tool_name, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tool_calls ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                try:
                    d["metadata"] = json.loads(d.get("metadata", "{}"))
                except (json.JSONDecodeError, TypeError):
                    d["metadata"] = {}
                results.append(d)
            return results
        except Exception as exc:
            logger.debug("Analytics recent-calls query failed: %s", exc)
        return []

    def get_failure_rate(self, tool_name: str) -> float:
        """Return failure rate (0.0 to 1.0) for a tool."""
        metrics = self.get_metrics(tool_name)
        total = metrics.get("total_calls", 0)
        if total == 0:
            return 0.0
        return metrics.get("total_failures", 0) / total

    def get_avg_cost(self, tool_name: str) -> float:
        """Return average cost per call for a tool."""
        metrics = self.get_metrics(tool_name)
        total = metrics.get("total_calls", 0)
        if total == 0:
            return 0.0
        return metrics.get("total_cost", 0) / total

    def get_avg_duration(self, tool_name: str) -> float:
        """Return average duration in ms for a tool."""
        metrics = self.get_metrics(tool_name)
        total = metrics.get("total_calls", 0)
        if total == 0:
            return 0.0
        return metrics.get("total_duration_ms", 0) / total

    def record_relationship(
        self, tool_a: str, tool_b: str, success: bool,
    ) -> None:
        """Record a tool_a → tool_b transition with success/failure."""
        now = time.time()
        try:
            conn = self._get_conn()
            existing = conn.execute(
                "SELECT frequency, total_success, total_failures, success_rate "
                "FROM tool_relationships WHERE tool_a = ? AND tool_b = ?",
                (tool_a, tool_b),
            ).fetchone()
            if existing:
                freq = existing[0] + 1
                tot_succ = existing[1] + (1 if success else 0)
                tot_fail = existing[2] + (0 if success else 1)
                srate = tot_succ / freq if freq > 0 else 0.0
                conn.execute(
                    "UPDATE tool_relationships SET frequency=?, success_rate=?, "
                    "total_success=?, total_failures=?, last_seen=? "
                    "WHERE tool_a = ? AND tool_b = ?",
                    (freq, srate, tot_succ, tot_fail, now, tool_a, tool_b),
                )
            else:
                conn.execute(
                    "INSERT INTO tool_relationships "
                    "(tool_a, tool_b, frequency, success_rate, total_success, "
                    " total_failures, first_seen, last_seen) "
                    "VALUES (?, ?, 1, ?, ?, ?, ?, ?)",
                    (
                        tool_a, tool_b,
                        1.0 if success else 0.0,
                        1 if success else 0,
                        0 if success else 1,
                        now, now,
                    ),
                )
            conn.commit()
        except Exception as exc:
            logger.debug("Relationship write failed: %s", exc)

    def get_relationships(
        self, tool_name: str, limit: int = 20,
    ) -> list:
        """Return tools most frequently called *after* tool_name."""
        try:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT tool_b, frequency, success_rate "
                "FROM tool_relationships WHERE tool_a = ? "
                "ORDER BY frequency DESC LIMIT ?",
                (tool_name, limit),
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.debug("Relationship query failed: %s", exc)
            return []

    def get_workflows(self, min_frequency: int = 2, limit: int = 20) -> list:
        """Return most common tool pairings (both directions)."""
        try:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT ta.tool_a, ta.tool_b, ta.frequency, ta.success_rate "
                "FROM tool_relationships ta "
                "WHERE ta.frequency >= ? "
                "ORDER BY ta.frequency DESC LIMIT ?",
                (min_frequency, limit),
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.debug("Workflows query failed: %s", exc)
            return []

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None


analytics_store = AnalyticsStore()
