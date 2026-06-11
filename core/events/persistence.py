"""Optional event persistence layer.

When enabled, every event published on the bus is written to a SQLite
store so it can be replayed for audit, debugging, or test scenarios.

Subscribes to *all* events via ``subscribe_all()``.
"""

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from .bus import event_bus
from .events import Event

logger = logging.getLogger(__name__)

_EVENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    source TEXT DEFAULT '',
    timestamp REAL NOT NULL,
    data TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
"""


class EventPersistence:
    """SQLite-backed persistence for all bus events.

    Thread-safe with WAL mode and per-thread connections.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            try:
                from gogeta_constants import get_gogeta_home
                base = get_gogeta_home() / "events"
            except ImportError:
                base = Path.home() / ".gogeta" / "events"
            base.mkdir(parents=True, exist_ok=True)
            db_path = base / "event_log.db"
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
            conn.executescript(_EVENT_SCHEMA)
            conn.commit()

    def write_event(self, event: Event) -> None:
        try:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO events (event_type, source, timestamp, data, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    event.type.value,
                    event.source,
                    event.timestamp,
                    json.dumps(event.data, default=str),
                    json.dumps(event.metadata, default=str),
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.debug("Event persistence write failed: %s", exc)

    def replay(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """Return stored events for replay. Oldest first."""
        try:
            conn = self._get_conn()
            if event_type:
                rows = conn.execute(
                    "SELECT * FROM events WHERE event_type = ? "
                    "ORDER BY timestamp ASC LIMIT ? OFFSET ?",
                    (event_type, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM events ORDER BY timestamp ASC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.debug("Event replay failed: %s", exc)
            return []

    def start(self) -> None:
        """Subscribe to all bus events and persist them."""
        event_bus.subscribe_all(self._on_event, priority=-100)

    def _on_event(self, event: Event) -> None:
        self.write_event(event)


event_persistence = EventPersistence()
