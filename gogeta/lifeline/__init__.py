"""Lifeline — Gogeta's persistent identity layer.

Not memory. Not sessions. Identity.

Files managed:
    SOUL.md         — Core identity (purpose, principles). Rarely changes.
    USER.md         — User profile (preferences, priorities).
    TIMELINE.md     — Chronological history of everything built.
    MEMORIES.md     — Important remembered facts (deduplicated).
    WORLDSTATE.md   — Current understanding of project state.
    MISSIONS.md     — Long-term goals and missions.
    FAILURES.md     — Failure log (what went wrong, why, how fixed).
    DECISIONS.md    — Architecture decisions (context, alternatives).
    REFLECTIONS/    — Auto-generated reflection files per session/task.
"""

from .lifeline import LifelineManager

__all__ = ["LifelineManager"]
