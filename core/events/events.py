"""Event types and dataclasses for the unified event bus.

Every system in Gogeta emits typed events through the bus rather than
calling each other directly. This decouples tools, providers, sessions,
memory, analytics, cost tracking, documentation, and lifeline from one
another.

Event type naming convention: ``<domain>.<action>``
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class EventType(str, Enum):
    """All event types the bus supports.

    When adding a new event type, use the ``<domain>.<action>`` naming.
    """

    # ── Tool lifecycle ──────────────────────────────────────────────
    TOOL_STARTED = "tool.started"
    TOOL_FINISHED = "tool.finished"
    TOOL_FAILED = "tool.failed"

    # ── Session lifecycle ───────────────────────────────────────────
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"

    # ── Provider (LLM) lifecycle ────────────────────────────────────
    PROVIDER_REQUESTED = "provider.requested"
    PROVIDER_SELECTED = "provider.selected"
    PROVIDER_COMPLETED = "provider.completed"
    PROVIDER_FAILED = "provider.failed"
    PROVIDER_FALLBACK = "provider.fallback"

    # ── Message flow ────────────────────────────────────────────────
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"

    # ── Agent lifecycle ─────────────────────────────────────────────
    AGENT_CREATED = "agent.created"
    AGENT_DESTROYED = "agent.destroyed"

    # ── Sub-agent lifecycle ─────────────────────────────────────────
    SUBAGENT_CREATED = "subagent.created"
    SUBAGENT_FINISHED = "subagent.finished"

    # ── Skill lifecycle ─────────────────────────────────────────────
    SKILL_EXECUTED = "skill.executed"
    SKILL_CREATED = "skill.created"

    # ── Project intelligence ────────────────────────────────────────
    PROJECT_UPDATED = "project.updated"

    # ── Memory operations ───────────────────────────────────────────
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"

    # ── Lifeline / reflection ───────────────────────────────────────
    REFLECTION_CREATED = "reflection.created"

    # ── Knowledge gaps (Law 1) ─────────────────────────────────────
    KNOWLEDGE_GAP_DETECTED = "knowledge_gap.detected"
    KNOWLEDGE_GAP_FILLED = "knowledge_gap.filled"
    CONFIDENCE_LOW = "confidence.low"

    # ── Self-configuration (Law 2) ──────────────────────────────────
    SYSTEM_CONFIGURED = "system.configured"


@dataclass
class Event:
    """An immutable event flowing through the bus.

    Attributes:
        type: The event type discriminator.
        data: Payload dict — contents vary by event type.
        source: Identifier of the emitting system (e.g. ``execution``).
        timestamp: Unix timestamp of emission. Auto-set if 0.
        metadata: Optional free-form metadata for middleware / subscribers.
        priority: Subscriber dispatch order (higher = earlier).
    """

    type: EventType
    data: Dict[str, Any]
    source: str = ""
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
