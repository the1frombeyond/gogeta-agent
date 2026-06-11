"""Project Intelligence — auto-maintains project documentation from events.

Powered by the Event Bus. Every significant action (tool finished, session
ended, file modified) flows through ``core/events/`` and lands here.

Files managed:
    project.md        — Current goal, status, active work, completed items
    decision_log.md   — Every decision with context, alternatives, tradeoffs
    tasks.md          — Task tracking (auto-updated from events)
    architecture.md   — Component documentation (planned)
"""

from .project import ProjectManager
from .decisions import DecisionLog
from .tasks import TaskManager
from .architecture import ArchitectureManager
from .subscriber import ProjectIntelligence

__all__ = [
    "ProjectManager",
    "DecisionLog",
    "TaskManager",
    "ArchitectureManager",
    "ProjectIntelligence",
]
