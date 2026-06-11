"""Built-in event subscribers that attach to the event bus.

Each subscriber class registers itself with the bus on construction and
reacts to events asynchronously (in-process, synchronous dispatch).

Current subscribers:

- ``AnalyticsSubscriber`` — records tool execution telemetry to the
  analytics store and tracks tool-to-tool relationship chains.
- ``CostSubscriber`` — listens for provider completions and updates
  cost intelligence data.
- ``DocumentationSubscriber`` — auto-updates ``project.md``,
  ``decision_log.md``, ``architecture.md`` when key events occur.
- ``LifelineSubscriber`` — feeds important events into lifeline for
  reflection and identity tracking.
"""

import json
import logging
import time
from typing import Optional

from .bus import event_bus
from .events import Event, EventType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Analytics subscriber
# ---------------------------------------------------------------------------

class AnalyticsSubscriber:
    """Records tool execution data to the analytics store via bus events.

    Instead of ``execute_tool()`` calling analytics directly, it emits
    ``TOOL_FINISHED`` / ``TOOL_FAILED`` events and this subscriber
    handles persistence.

    Also tracks tool → tool relationship chains by recording the
    previous tool call alongside each new call.
    """

    def __init__(self):
        self._last_tool: Optional[str] = None
        event_bus.subscribe(EventType.TOOL_FINISHED, self._on_tool_finished)
        event_bus.subscribe(EventType.TOOL_FAILED, self._on_tool_failed)

    def _on_tool_finished(self, event: Event) -> None:
        data = event.data
        self._record(data)
        self._record_relationship(
            data.get("name", ""),
            data.get("success", True),
        )

    def _on_tool_failed(self, event: Event) -> None:
        data = event.data
        self._record(data)
        self._record_relationship(
            data.get("name", ""),
            success=False,
        )

    def _record(self, data: dict) -> None:
        try:
            from tools.analytics import analytics_store, ToolCallRecord
            record = ToolCallRecord(
                tool_name=data.get("name", ""),
                category=data.get("category", ""),
                session_id=data.get("session_id", ""),
                agent_id=data.get("agent_id", ""),
                provider=data.get("provider", ""),
                duration_ms=data.get("duration_ms", 0.0),
                success=data.get("success", True),
                error=data.get("error", "")[:500],
                tokens_input=data.get("tokens_input", 0),
                tokens_output=data.get("tokens_output", 0),
                cost=data.get("cost", 0.0),
                timestamp=data.get("timestamp", time.time()),
                metadata=data.get("metadata", {}),
            )
            analytics_store.record_call(record)
        except Exception as exc:
            logger.debug("AnalyticsSubscriber record failed: %s", exc)

    def _record_relationship(self, tool_name: str, success: bool) -> None:
        """Track tool_a → tool_b transitions with frequency and success rate."""
        if not tool_name or not self._last_tool:
            self._last_tool = tool_name
            return

        tool_a, tool_b = self._last_tool, tool_name
        self._last_tool = tool_name

        try:
            from tools.analytics import analytics_store
            analytics_store.record_relationship(
                tool_a=tool_a,
                tool_b=tool_b,
                success=success,
            )
        except Exception as exc:
            logger.debug("Relationship record failed: %s", exc)


# ---------------------------------------------------------------------------
# Cost subscriber
# ---------------------------------------------------------------------------

class CostSubscriber:
    """Tracks provider cost from ``PROVIDER_COMPLETED`` events.

    Updates the cost intelligence system (``gateway/cost_intelligence.py``)
    and maintains an in-memory session cost total.
    """

    def __init__(self):
        self._session_cost: float = 0.0
        event_bus.subscribe(EventType.PROVIDER_COMPLETED, self._on_provider_completed)
        event_bus.subscribe(EventType.TOOL_FINISHED, self._on_tool_finished)

    def _on_provider_completed(self, event: Event) -> None:
        data = event.data
        provider = data.get("provider", "")
        cost = data.get("cost", 0.0)
        tokens_in = data.get("tokens_input", 0)
        tokens_out = data.get("tokens_output", 0)

        self._session_cost += cost

        try:
            from gateway.cost_intelligence import record_provider_usage
            record_provider_usage(
                provider=provider,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                cost=cost,
                session_id=data.get("session_id", ""),
            )
        except ImportError:
            pass
        except Exception as exc:
            logger.debug("Cost subscriber provider recording failed: %s", exc)

    def _on_tool_finished(self, event: Event) -> None:
        data = event.data
        cost = data.get("cost", 0.0)
        if cost:
            self._session_cost += cost

    @property
    def session_cost(self) -> float:
        return self._session_cost

    def reset_session_cost(self) -> None:
        self._session_cost = 0.0


# ---------------------------------------------------------------------------
# Documentation subscriber
# ---------------------------------------------------------------------------

class DocumentationSubscriber:
    """Auto-updates project documentation when key events occur.

    Delegates to ``ProjectIntelligence`` (``core/intelligence/``) for the
    actual file-writing. This class is a thin adapter that bridges the
    event bus to the intelligence subsystem.
    """

    def __init__(self, enabled: bool = False):
        self._enabled = enabled
        self._intel = None
        if enabled:
            from core.intelligence import ProjectIntelligence
            self._intel = ProjectIntelligence(auto_start=True)

    @property
    def intel(self):
        return self._intel


# ---------------------------------------------------------------------------
# Lifeline subscriber
# ---------------------------------------------------------------------------

class GenomeSubscriber:
    """Runs genome learning on session boundaries.

    Triggered by ``SESSION_ENDED`` to discover workflows, detect
    patterns, evolve skills, and learn from failures.

    Also subscribes to ``TOOL_FINISHED`` at low priority to collect
    session-level tool data for the learning pipeline.
    """

    def __init__(self, enabled: bool = False):
        self._enabled = enabled
        self._genome = None
        if enabled:
            from gogeta.genome import GenomeManager
            self._genome = GenomeManager()
            event_bus.subscribe(EventType.SESSION_ENDED, self._on_session_ended, priority=-20)
            event_bus.subscribe(EventType.TOOL_FINISHED, self._on_tool_finished, priority=-20)

    @property
    def genome(self):
        return self._genome

    def _on_tool_finished(self, event: Event) -> None:
        pass

    def _on_session_ended(self, event: Event) -> None:
        if not self._genome:
            return
        try:
            from tools.analytics import analytics_store
            self._genome._analytics = analytics_store
            stats = self._genome.learn()
            self._genome.report()
            logger.info(
                "Genome learned: %d workflows, %d patterns, %d skills, %d rules",
                stats.get("workflows", 0),
                stats.get("patterns", 0),
                stats.get("new_skills", 0),
                stats.get("new_rules", 0),
            )
        except Exception as exc:
            logger.debug("Genome learning failed: %s", exc)


class LifelineSubscriber:
    """Feeds important events into lifeline for reflection.

    Listens for tool events, session events, and project updates to
    automatically maintain ``gogeta/lifeline/TIMELINE.md``,
    ``MEMORIES.md``, ``WORLDSTATE.md``, and ``REFLECTIONS/``.
    """

    def __init__(self, enabled: bool = False):
        self._enabled = enabled
        self._lifeline = None
        if enabled:
            from gogeta.lifeline import LifelineManager
            self._lifeline = LifelineManager()
            self._lifeline.ensure_soul()
            self._session_files: list = []
            event_bus.subscribe(EventType.TOOL_FINISHED, self._on_tool_finished, priority=-10)
            event_bus.subscribe(EventType.TOOL_FAILED, self._on_tool_failed, priority=-10)
            event_bus.subscribe(EventType.SESSION_STARTED, self._on_session_started, priority=-10)
            event_bus.subscribe(EventType.SESSION_ENDED, self._on_session_ended, priority=-10)
            event_bus.subscribe(EventType.PROJECT_UPDATED, self._on_project_updated, priority=-10)
            event_bus.subscribe(EventType.REFLECTION_CREATED, self._on_reflection_created, priority=-10)
            event_bus.subscribe(EventType.SUBAGENT_FINISHED, self._on_subagent_finished, priority=-10)

    @property
    def lifeline(self):
        return self._lifeline

    def _on_tool_finished(self, event: Event) -> None:
        data = event.data
        name = data.get("name", "")
        args = data.get("args", {})
        if name in ("write_file", "edit_file", "patch"):
            fp = args.get("file_path", args.get("path", ""))
            if fp:
                self._session_files.append(fp)
                self._lifeline.update_worldstate("Files Modified", fp)

        if name in ("write_file", "edit_file", "patch", "run_tests"):
            self._lifeline.add_memory("tools", f"{name} completed successfully")

    def _on_tool_failed(self, event: Event) -> None:
        data = event.data
        name = data.get("name", "")
        error = data.get("error", "unknown")
        self._lifeline.add_failure(
            attempt=name,
            problem=error,
            solution="diagnose and retry",
            lesson="Tools can fail — build retry logic",
        )

    def _on_session_started(self, event: Event) -> None:
        self._session_files = []
        self._lifeline.update_worldstate("Session", "Active")

    def _on_session_ended(self, event: Event) -> None:
        data = event.data
        session_id = data.get("session_id", "unknown")
        summary = data.get("summary", f"Session {session_id}")
        self._lifeline.add_timeline_entry(
            title=summary,
            files=self._session_files if self._session_files else None,
            outcome="Session completed",
        )
        self._session_files = []
        self._lifeline.update_worldstate("Session", "Idle")

    def _on_project_updated(self, event: Event) -> None:
        data = event.data
        for key, val in data.items():
            self._lifeline.update_worldstate(key.replace("_", " ").title(), str(val))

    def _on_reflection_created(self, event: Event) -> None:
        data = event.data
        title = data.get("title", "Auto Reflection")
        body = data.get("body", "") or data.get("decision", str(data))
        self._lifeline.add_reflection(title=title, body=body)

    def _on_subagent_finished(self, event: Event) -> None:
        data = event.data
        goal = data.get("goal", "Unknown task")
        result = data.get("result", "")
        self._lifeline.add_timeline_entry(
            title=f"Sub-agent: {goal}",
            outcome="Completed" if data.get("success", True) else "Failed",
            details=result,
        )


# ---------------------------------------------------------------------------
# Gogeta context subscriber
# ---------------------------------------------------------------------------

class ContextSubscriber:
    """Auto-updates the Gogeta SESSION_SUMMARY.md from bus events.

    Subscribes to tool and session lifecycle events to incrementally
    maintain the anchored session summary used by ContextBuilder for
    system-prompt augmentation.

    This is the write-side of ``agent/context/summarizer.py`` — it
    feeds real-time event data into the structured summary file.
    """

    def __init__(self):
        self._summarizer = None
        try:
            from agent.context.summarizer import SessionSummarizer
            self._summarizer = SessionSummarizer()
            event_bus.subscribe(EventType.TOOL_FINISHED, self._on_tool_finished, priority=-15)
            event_bus.subscribe(EventType.TOOL_FAILED, self._on_tool_failed, priority=-15)
            event_bus.subscribe(EventType.SESSION_STARTED, self._on_session_started, priority=-15)
            event_bus.subscribe(EventType.SESSION_ENDED, self._on_session_ended, priority=-15)
            event_bus.subscribe(EventType.REFLECTION_CREATED, self._on_reflection_created, priority=-15)
        except Exception as exc:
            logger.debug("ContextSubscriber init failed: %s", exc)

    @property
    def summarizer(self):
        return self._summarizer

    def _on_tool_finished(self, event: Event) -> None:
        if not self._summarizer:
            return
        data = event.data
        name = data.get("name", "")

        # Track file modifications
        args = data.get("args", {})
        fp = args.get("file_path", args.get("path", ""))
        if fp:
            self._summarizer.add_file_changed(fp)

        # Track completed milestones
        if name in ("write_file", "edit_file", "patch", "run_tests"):
            self._summarizer.add_completed(f"{name} {fp or ''}".strip())

    def _on_tool_failed(self, event: Event) -> None:
        if not self._summarizer:
            return
        data = event.data
        name = data.get("name", "")
        error = data.get("error", "unknown")
        self._summarizer.add_open_question(f"Tool '{name}' failed: {error[:200]}")

    def _on_session_started(self, event: Event) -> None:
        if not self._summarizer:
            return
        self._summarizer.reset()

    def _on_session_ended(self, event: Event) -> None:
        if not self._summarizer:
            return
        data = event.data
        summary = data.get("summary", "Session ended")
        self._summarizer.set_remaining_work(summary)

    def _on_reflection_created(self, event: Event) -> None:
        if not self._summarizer:
            return
        data = event.data
        decision = data.get("decision", data.get("title", ""))
        if decision:
            self._summarizer.add_decision(decision)


# ---------------------------------------------------------------------------
# Knowledge gap subscriber (Law 1)
# ---------------------------------------------------------------------------

class KnowledgeGapSubscriber:
    """Tracks knowledge gap detection events for analytics and learning.

    Monitors gap frequency, confidence trends, and research pass rates
    to help the genome evolve better fact-checking behaviour.
    """

    def __init__(self):
        self._total_gaps = 0
        self._total_research_passes = 0
        self._confidence_scores: list = []
        event_bus.subscribe(EventType.KNOWLEDGE_GAP_DETECTED, self._on_gap_detected, priority=-15)
        event_bus.subscribe(EventType.CONFIDENCE_LOW, self._on_confidence_low, priority=-15)

    def _on_gap_detected(self, event: Event) -> None:
        data = event.data
        gap_count = data.get("gap_count", 0)
        research_count = data.get("research_count", 0)
        confidence = data.get("confidence", 1.0)

        self._total_gaps += gap_count
        if research_count:
            self._total_research_passes += 1
        self._confidence_scores.append(confidence)

        logger.info(
            "Knowledge gaps: %d gaps, confidence=%.2f, research=%d",
            gap_count, confidence, research_count,
        )

    def _on_confidence_low(self, event: Event) -> None:
        data = event.data
        confidence = data.get("confidence", 0.0)
        logger.warning(
            "Low confidence response: confidence=%.2f, gaps=%d",
            confidence, data.get("gap_count", 0),
        )

    @property
    def stats(self) -> dict:
        avg_conf = (
            sum(self._confidence_scores) / len(self._confidence_scores)
            if self._confidence_scores else 1.0
        )
        return {
            "total_gaps": self._total_gaps,
            "total_research_passes": self._total_research_passes,
            "avg_confidence": round(avg_conf, 3),
            "detection_count": len(self._confidence_scores),
        }


# ---------------------------------------------------------------------------
# Skill evolution subscriber (Law 3)
# ---------------------------------------------------------------------------

class SkillEvolutionSubscriber:
    """Runs the skill evolution audit cycle on session boundaries.

    Listens for ``SESSION_ENDED`` and checks if the 3-day audit interval
    has elapsed. If so, runs the full SkillEvolutionEngine audit:

      - Gathers snapshots of skills, tools, workflows, and subagents
      - Runs the genome learning pipeline
      - Analyzes for failures, bottlenecks, and improvement candidates
      - Generates concrete improvements via LLM
      - Deploys approved improvements (skill archive/optimize/create)

    Also subscribes to ``KNOWLEDGE_GAP_FILLED`` as a secondary trigger
    — repeated gaps may indicate a skill deficiency worth auditing.
    """

    def __init__(self, enabled: bool = False, dry_run: bool = False):
        self._enabled = enabled
        self._dry_run = dry_run
        self._engine = None
        if enabled:
            from agent.skill_evolution import SkillEvolutionEngine
            from gogeta.genome import GenomeManager
            self._engine = SkillEvolutionEngine(
                genome_manager=GenomeManager(),
                deploy_enabled=not dry_run,
            )
            event_bus.subscribe(EventType.SESSION_ENDED, self._on_session_ended, priority=-25)
            event_bus.subscribe(EventType.KNOWLEDGE_GAP_FILLED, self._on_gap_filled, priority=-25)

    @property
    def engine(self):
        return self._engine

    @property
    def last_report(self):
        return self._engine._last_report if self._engine else None

    def _on_session_ended(self, event: Event) -> None:
        if not self._engine:
            return
        if not self._engine.should_run_now():
            return
        report = self._engine.run_audit()
        if report.error:
            logger.warning("Skill evolution audit failed: %s", report.error)
        elif report.improvements:
            logger.info(
                "Skill evolution: %d improvements, %d deployed, summary: %s",
                len(report.improvements),
                report.deployed_count,
                report.summary,
            )

    def _on_gap_filled(self, event: Event) -> None:
        """Secondary trigger — knowledge gaps may indicate skill deficiencies."""
        pass  # reserved for future use


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def start_default_subscribers(
    analytics: bool = True,
    cost: bool = True,
    documentation: bool = False,
    lifeline: bool = False,
    genome: bool = False,
    context: bool = True,
    knowledge_gaps: bool = True,
    skill_evolution: bool = False,
) -> dict:
    """Create and return all requested subscribers.

    Returns a dict mapping subscriber name to instance so callers can
    access properties (e.g. ``subscribers["cost"].session_cost``).
    """
    instances = {}
    if analytics:
        instances["analytics"] = AnalyticsSubscriber()
    if cost:
        instances["cost"] = CostSubscriber()
    if documentation:
        instances["documentation"] = DocumentationSubscriber(enabled=True)
    if lifeline:
        instances["lifeline"] = LifelineSubscriber(enabled=True)
    if genome:
        instances["genome"] = GenomeSubscriber(enabled=True)
    if context:
        instances["context"] = ContextSubscriber()
    if knowledge_gaps:
        instances["knowledge_gaps"] = KnowledgeGapSubscriber()
    if skill_evolution:
        instances["skill_evolution"] = SkillEvolutionSubscriber(enabled=True)
    return instances
