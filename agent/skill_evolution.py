"""Skill Evolution Engine — Law 3 of the Gogeta Autonomy Directive.

Continuous audit every 3 days covering Skills, Tools, Prompts, Workflows,
and Agents. Detects usage patterns, failure modes, bottlenecks, and
automatically generates, tests, and deploys improvements.

Builds on the existing genome pipeline (workflow discovery, pattern
detection, skill evolution) and extends it with tool-analysis, prompt
analysis, subagent analysis, and an automated improvement loop.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.events.bus import event_bus
from core.events.events import Event, EventType

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

DEFAULT_AUDIT_INTERVAL_DAYS = 3
"""How often the full audit cycle runs."""

MIN_TOOL_CALLS_FOR_ANALYSIS = 10
"""Minimum tool calls needed before patterns are statistically meaningful."""

ANALYSIS_SYSTEM_PROMPT = (
    "You are a skill evolution analyst. Your job is to analyze usage "
    "statistics for skills, tools, and workflows, then suggest concrete "
    "improvements. Focus on:\n"
    "  1. Failure patterns — tools or skills that fail repeatedly\n"
    "  2. Bottlenecks — slow or overused tools\n"
    "  3. Redundancy — tools that overlap or duplicate each other\n"
    "  4. Gaps — missing capabilities that would speed up common tasks\n"
    "  5. Consolidation — skills that should be merged or split\n\n"
    "Return a JSON object with:\n"
    '  - "improvements": list of improvement objects, each with:\n'
    '    - "type": "skill" | "tool" | "prompt" | "workflow" | "agent"\n'
    '    - "target": name of the item to improve\n'
    '    - "action": "merge" | "archive" | "create" | "optimize" | "deprecate"\n'
    '    - "rationale": why this change is needed\n'
    '    - "suggested_content": what to create or change (for skills/prompts)\n'
    '    - "priority": 1-5 (5 = highest)\n'
    '  - "bottlenecks": list of identified bottleneck descriptions\n'
    '  - "summary": one-line summary of the audit findings'
)


# ── Data structures ────────────────────────────────────────────────────


@dataclass
class AuditSnapshot:
    """Snapshot of all auditable surfaces at a point in time."""
    skills: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    workflows: List[Dict[str, Any]] = field(default_factory=list)
    subagents: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class Improvement:
    type: str  # skill, tool, prompt, workflow, agent
    target: str
    action: str  # merge, archive, create, optimize, deprecate
    rationale: str
    suggested_content: str = ""
    priority: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "target": self.target,
            "action": self.action,
            "rationale": self.rationale,
            "suggested_content": self.suggested_content[:200] if self.suggested_content else "",
            "priority": self.priority,
        }


@dataclass
class AuditReport:
    snapshot: AuditSnapshot = field(default_factory=AuditSnapshot)
    improvements: List[Improvement] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)
    summary: str = ""
    deployed_count: int = 0
    failed_count: int = 0
    elapsed_seconds: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "improvements": [i.to_dict() for i in self.improvements],
            "bottlenecks": self.bottlenecks,
            "summary": self.summary,
            "deployed": self.deployed_count,
            "failed": self.failed_count,
            "elapsed": round(self.elapsed_seconds, 2),
        }


# ── Evolution Engine ───────────────────────────────────────────────────


class SkillEvolutionEngine:
    """Orchestrates the 3-day audit cycle across all five surfaces.

    The engine:
      1. Gathers usage snapshots (skills, tools, workflows, agents)
      2. Runs the genome learning pipeline
      3. Analyzes for failures, bottlenecks, and improvement candidates
      4. Generates concrete improvements via LLM
      5. Tests improvements in dry-run mode
      6. Deploys approved improvements
    """

    def __init__(
        self,
        genome_manager: Optional[Any] = None,
        call_llm: Optional[Callable] = None,
        deploy_enabled: bool = True,
    ):
        self._genome = genome_manager
        self._call_llm = call_llm
        self._deploy_enabled = deploy_enabled
        self._last_report: Optional[AuditReport] = None
        self._run_count = 0

    # ── Public API ────────────────────────────────────────────────────

    def run_audit(
        self,
        force: bool = False,
        dry_run: bool = False,
    ) -> AuditReport:
        """Execute a full audit cycle.

        Args:
            force: Skip the interval check.
            dry_run: Analyze and report but do not deploy.

        Returns:
            AuditReport with improvements and deployment results.
        """
        start = time.monotonic()
        self._run_count += 1
        report = AuditReport()

        try:
            snapshot = self._gather_snapshot()
            report.snapshot = snapshot

            genome_stats = self._run_genome_pipeline()
            logger.info("Genome pipeline: %s", genome_stats)

            improvements = self._analyze(snapshot)
            report.improvements = improvements
            report.bottlenecks = self._find_bottlenecks(snapshot)

            if not improvements:
                report.summary = "No improvements needed — all surfaces healthy"
            elif dry_run or not self._deploy_enabled:
                report.summary = (
                    f"Found {len(improvements)} improvement candidates "
                    f"({len(report.bottlenecks)} bottlenecks) — dry run, no changes applied"
                )
            else:
                deployed = self._deploy_improvements(improvements, snapshot)
                report.deployed_count = deployed
                report.failed_count = len(improvements) - deployed
                report.summary = (
                    f"Audit complete: {len(improvements)} improvements found, "
                    f"{deployed} deployed, {len(improvements) - deployed} skipped/failed"
                )

            self._write_last_run()
            self._log_audit(report)

        except Exception as exc:
            logger.exception("Skill evolution audit failed")
            report.error = str(exc)
            report.summary = f"Audit failed: {exc}"

        report.elapsed_seconds = time.monotonic() - start
        self._last_report = report
        return report

    def should_run_now(self) -> bool:
        """Check if the audit interval has elapsed."""
        last_audit = self._read_last_run()
        if last_audit is None:
            return True
        return (datetime.now() - last_audit) > timedelta(days=DEFAULT_AUDIT_INTERVAL_DAYS)

    @staticmethod
    def _last_run_path() -> Path:
        """Path to the audit timestamp file in the genome directory."""
        from gogeta.genome.storage import GenomeStorage
        storage = GenomeStorage()
        return storage._dir / ".evolution_audit_timestamp"

    def _read_last_run(self) -> Optional[datetime]:
        """Read the last audit timestamp from disk."""
        path = self._last_run_path()
        try:
            if path.exists():
                ts = float(path.read_text().strip())
                return datetime.fromtimestamp(ts)
        except Exception:
            pass
        return None

    def _write_last_run(self) -> None:
        """Persist the current timestamp so should_run_now() sees it."""
        try:
            path = self._last_run_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(time.time()))
        except Exception as exc:
            logger.debug("Failed to write audit timestamp: %s", exc)

    # ── Step 1: Gather snapshot ──────────────────────────────────────

    def _gather_snapshot(self) -> AuditSnapshot:
        """Collect current state of all auditable surfaces."""
        snapshot = AuditSnapshot(timestamp=time.time())

        snapshot.skills = self._gather_skills_snapshot()
        snapshot.tools = self._gather_tools_snapshot()
        snapshot.workflows = self._gather_workflows_snapshot()
        snapshot.subagents = self._gather_subagents_snapshot()

        return snapshot

    def _gather_skills_snapshot(self) -> List[Dict[str, Any]]:
        """Get usage stats for all curator-managed skills."""
        try:
            from tools.skill_usage import agent_created_report, usage_report
            return agent_created_report() or []
        except Exception as exc:
            logger.debug("Skills snapshot failed: %s", exc)
            return []

    def _gather_tools_snapshot(self) -> List[Dict[str, Any]]:
        """Get tool call stats from analytics store."""
        try:
            from tools.analytics import analytics_store
            calls = analytics_store.get_recent_calls(limit=500) or []

            tool_stats: Dict[str, Dict] = {}
            for c in calls:
                name = c.get("tool_name", c.get("name", ""))
                if not name:
                    continue
                if name not in tool_stats:
                    tool_stats[name] = {
                        "name": name,
                        "calls": 0,
                        "failures": 0,
                        "total_duration_ms": 0.0,
                    }
                tool_stats[name]["calls"] += 1
                if not c.get("success", True):
                    tool_stats[name]["failures"] += 1
                tool_stats[name]["total_duration_ms"] += c.get("duration_ms", 0.0)

            result = []
            for name, stats in tool_stats.items():
                avg_ms = stats["total_duration_ms"] / max(stats["calls"], 1)
                result.append({
                    "name": name,
                    "calls": stats["calls"],
                    "failure_rate": round(stats["failures"] / max(stats["calls"], 1), 3),
                    "avg_duration_ms": round(avg_ms, 1),
                })

            return sorted(result, key=lambda x: x["calls"], reverse=True)
        except Exception as exc:
            logger.debug("Tools snapshot failed: %s", exc)
            return []

    def _gather_workflows_snapshot(self) -> List[Dict[str, Any]]:
        """Get workflow data from genome storage."""
        try:
            from gogeta.genome.storage import GenomeStorage
            storage = GenomeStorage()
            return storage.load_workflows() or []
        except Exception as exc:
            logger.debug("Workflows snapshot failed: %s", exc)
            return []

    def _gather_subagents_snapshot(self) -> List[Dict[str, Any]]:
        """Get sub-agent delegation stats."""
        try:
            from tools.analytics import analytics_store
            calls = analytics_store.get_recent_calls(limit=200) or []
            delegate_calls = [
                c for c in calls
                if c.get("tool_name", "").startswith("delegate_")
            ]
            result = []
            for c in delegate_calls:
                result.append({
                    "tool": c.get("tool_name", ""),
                    "success": c.get("success", True),
                    "duration_ms": c.get("duration_ms", 0.0),
                    "error": c.get("error", ""),
                })
            return result
        except Exception as exc:
            logger.debug("Subagent snapshot failed: %s", exc)
            return []

    # ── Step 2: Run genome pipeline ──────────────────────────────────

    def _run_genome_pipeline(self) -> Dict[str, int]:
        """Run the existing genome learning pipeline."""
        try:
            if self._genome:
                return self._genome.learn(force=True)
            from gogeta.genome import GenomeManager
            gm = GenomeManager()
            return gm.learn(force=True)
        except Exception as exc:
            logger.warning("Genome pipeline failed: %s", exc)
            return {"workflows": 0, "patterns": 0, "skills": 0, "rules": 0}

    # ── Step 3: Analyze ──────────────────────────────────────────────

    def _analyze(self, snapshot: AuditSnapshot) -> List[Improvement]:
        """Analyze snapshots and generate improvement candidates.

        Uses both heuristic rules and LLM analysis.
        """
        improvements: List[Improvement] = []

        improvements.extend(self._heuristic_skill_analysis(snapshot.skills))
        improvements.extend(self._heuristic_tool_analysis(snapshot.tools))
        improvements.extend(self._heuristic_workflow_analysis(snapshot.workflows))

        llm_improvements = self._llm_improvement_analysis(snapshot)
        improvements.extend(llm_improvements)

        deduplicated = self._deduplicate_improvements(improvements)
        return sorted(deduplicated, key=lambda i: i.priority, reverse=True)

    def _heuristic_skill_analysis(
        self,
        skills: List[Dict[str, Any]],
    ) -> List[Improvement]:
        """Rule-based skill analysis for obvious improvements."""
        improvements = []

        for skill in skills:
            name = skill.get("name", "")
            use_count = skill.get("use_count", 0)
            view_count = skill.get("view_count", 0)
            state = skill.get("state", "active")
            patch_count = skill.get("patch_count", 0)

            if state == "active" and use_count == 0 and view_count == 0:
                improvements.append(Improvement(
                    type="skill",
                    target=name,
                    action="archive",
                    rationale=f"Skill '{name}' has never been used or viewed",
                    priority=1,
                ))

            if patch_count > 5 and use_count < 3:
                improvements.append(Improvement(
                    type="skill",
                    target=name,
                    action="optimize",
                    rationale=f"Skill '{name}' has been patched {patch_count}x "
                              f"but only used {use_count}x — may need restructuring",
                    priority=3,
                ))

        return improvements

    def _heuristic_tool_analysis(
        self,
        tools: List[Dict[str, Any]],
    ) -> List[Improvement]:
        """Rule-based tool analysis for bottlenecks and failures."""
        improvements = []

        for tool in tools:
            name = tool.get("name", "")
            calls = tool.get("calls", 0)
            failure_rate = tool.get("failure_rate", 0.0)
            avg_ms = tool.get("avg_duration_ms", 0.0)

            if calls < MIN_TOOL_CALLS_FOR_ANALYSIS:
                continue

            if failure_rate > 0.3:
                improvements.append(Improvement(
                    type="tool",
                    target=name,
                    action="optimize",
                    rationale=f"Tool '{name}' has {failure_rate:.0%} failure rate "
                              f"({calls} calls)",
                    priority=5,
                ))

            if avg_ms > 10000:
                improvements.append(Improvement(
                    type="tool",
                    target=name,
                    action="optimize",
                    rationale=f"Tool '{name}' averages {avg_ms/1000:.1f}s per call "
                              f"({calls} calls) — potential bottleneck",
                    priority=4,
                ))

        return improvements

    def _heuristic_workflow_analysis(
        self,
        workflows: List[Dict[str, Any]],
    ) -> List[Improvement]:
        """Rule-based workflow analysis."""
        improvements = []

        for wf in workflows:
            name = wf.get("name", "unknown")
            confidence = wf.get("confidence", 0.0)
            executions = wf.get("executions", wf.get("frequency", 0))

            if confidence < 0.3 and executions > 5:
                improvements.append(Improvement(
                    type="workflow",
                    target=name,
                    action="optimize",
                    rationale=f"Workflow '{name}' has low confidence ({confidence:.2f}) "
                              f"despite {executions} executions — may need refinement",
                    priority=2,
                ))

        return improvements

    def _llm_improvement_analysis(
        self,
        snapshot: AuditSnapshot,
    ) -> List[Improvement]:
        """Use LLM to find improvement candidates beyond heuristic rules."""
        if not self._call_llm:
            return []

        try:
            prompt_parts = ["Current system state for evolution analysis:\n"]

            if snapshot.skills:
                prompt_parts.append("--- Skills ---")
                for s in snapshot.skills[:20]:
                    prompt_parts.append(
                        f"  {s.get('name', '?')}: "
                        f"uses={s.get('use_count', 0)}, "
                        f"views={s.get('view_count', 0)}, "
                        f"state={s.get('state', 'active')}"
                    )

            if snapshot.tools:
                prompt_parts.append("--- Tools (top 20 by calls) ---")
                for t in snapshot.tools[:20]:
                    prompt_parts.append(
                        f"  {t.get('name', '?')}: "
                        f"calls={t.get('calls', 0)}, "
                        f"failure={t.get('failure_rate', 0):.0%}, "
                        f"avg={t.get('avg_duration_ms', 0):.0f}ms"
                    )

            if snapshot.workflows:
                prompt_parts.append("--- Workflows (top 10) ---")
                for w in snapshot.workflows[:10]:
                    prompt_parts.append(
                        f"  {w.get('name', '?')}: "
                        f"conf={w.get('confidence', 0):.2f}"
                    )

            if snapshot.subagents:
                prompt_parts.append("--- Sub-agents ---")
                for s in snapshot.subagents[:10]:
                    prompt_parts.append(
                        f"  {s.get('tool', '?')}: "
                        f"success={s.get('success', True)}"
                    )

            prompt_parts.append(
                f"\nBased on this data, what improvements would you recommend?"
            )

            judge_messages = [
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(prompt_parts)},
            ]

            response = self._call_llm(
                task="evolution",
                messages=judge_messages,
                temperature=0.2,
                max_tokens=3000,
            )

            raw = response.choices[0].message.content or "{}"
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
                raw = raw.rsplit("\n", 1)[0] if "\n" in raw else raw
                raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

            parsed = json.loads(raw)
            raw_improvements = parsed.get("improvements", [])
            bottlenecks = parsed.get("bottlenecks", [])

            improvements = []
            for imp in raw_improvements:
                if not isinstance(imp, dict):
                    continue
                improvements.append(Improvement(
                    type=imp.get("type", "skill"),
                    target=imp.get("target", ""),
                    action=imp.get("action", "optimize"),
                    rationale=imp.get("rationale", ""),
                    suggested_content=imp.get("suggested_content", ""),
                    priority=int(imp.get("priority", 3)),
                ))

            return improvements

        except Exception as exc:
            logger.warning("LLM improvement analysis failed: %s", exc)
            return []

    @staticmethod
    def _deduplicate_improvements(
        improvements: List[Improvement],
    ) -> List[Improvement]:
        """Remove duplicate improvement suggestions for the same target."""
        seen: Dict[str, Improvement] = {}
        for imp in improvements:
            key = f"{imp.type}:{imp.target}:{imp.action}"
            if key not in seen or imp.priority > seen[key].priority:
                seen[key] = imp
        return list(seen.values())

    # ── Step 4: Find bottlenecks ─────────────────────────────────────

    def _find_bottlenecks(self, snapshot: AuditSnapshot) -> List[str]:
        """Identify system bottlenecks from tool stats."""
        bottlenecks = []

        for tool in snapshot.tools:
            name = tool.get("name", "")
            calls = tool.get("calls", 0)
            failure_rate = tool.get("failure_rate", 0.0)
            avg_ms = tool.get("avg_duration_ms", 0.0)

            if calls < MIN_TOOL_CALLS_FOR_ANALYSIS:
                continue

            if avg_ms > 15000:
                bottlenecks.append(
                    f"High latency: {name} averages {avg_ms/1000:.1f}s "
                    f"({calls} calls)"
                )
            elif failure_rate > 0.25:
                bottlenecks.append(
                    f"Unreliable: {name} has {failure_rate:.0%} failure rate "
                    f"({calls} calls)"
                )

        return bottlenecks

    # ── Step 5: Deploy improvements ──────────────────────────────────

    def _deploy_improvements(
        self,
        improvements: List[Improvement],
        snapshot: AuditSnapshot,
    ) -> int:
        """Deploy approved improvements to the system.

        Returns the number of successfully deployed improvements.
        """
        deployed = 0
        non_deployable_actions = {"deprecate"}

        for imp in improvements:
            if imp.action in non_deployable_actions:
                logger.info("Skipping non-deployable improvement: %s", imp.target)
                continue

            try:
                if self._try_deploy(imp):
                    deployed += 1
                    self._emit_deployment(imp, success=True)
                else:
                    self._emit_deployment(imp, success=False)
            except Exception as exc:
                logger.warning("Deploy failed for %s/%s: %s", imp.type, imp.target, exc)
                self._emit_deployment(imp, success=False, error=str(exc))

        return deployed

    def _try_deploy(self, improvement: Improvement) -> bool:
        """Attempt to deploy a single improvement.

        Routes to the appropriate handler based on type and action.
        """
        if improvement.type == "skill":
            return self._deploy_skill_improvement(improvement)

        elif improvement.type == "workflow":
            return self._deploy_workflow_improvement(improvement)

        elif improvement.type == "tool":
            logger.info("Tool improvement '%s' noted — requires code change", improvement.target)
            return False

        elif improvement.type == "agent":
            logger.info("Agent improvement '%s' noted", improvement.target)
            return False

        return False

    def _deploy_skill_improvement(self, improvement: Improvement) -> bool:
        """Deploy a skill-related improvement via skill_manage."""
        try:
            from tools.skill_manager_tool import skill_manage

            if improvement.action == "archive":
                result = json.loads(skill_manage(
                    action="delete",
                    name=improvement.target,
                    absorbed_into="",
                ))
                return result.get("success", False)

            elif improvement.action == "optimize" and improvement.suggested_content:
                result = json.loads(skill_manage(
                    action="edit",
                    name=improvement.target,
                    content=improvement.suggested_content,
                ))
                return result.get("success", False)

            elif improvement.action == "create" and improvement.suggested_content:
                result = json.loads(skill_manage(
                    action="create",
                    name=improvement.target,
                    content=improvement.suggested_content,
                ))
                return result.get("success", False)

            return False

        except Exception as exc:
            logger.warning("Skill deploy failed: %s", exc)
            return False

    def _deploy_workflow_improvement(self, improvement: Improvement) -> bool:
        """Store workflow improvements in the genome."""
        try:
            from gogeta.genome.storage import GenomeStorage
            storage = GenomeStorage()
            storage.add_evolution_entry({
                "event": "workflow_improved",
                "target": improvement.target,
                "action": improvement.action,
                "rationale": improvement.rationale,
                "timestamp": time.time(),
            })
            return True
        except Exception:
            return False

    # ── Event emission ───────────────────────────────────────────────

    @staticmethod
    def _emit_deployment(improvement: Improvement, success: bool, error: str = "") -> None:
        try:
            event_bus.emit(Event(
                type=EventType.SYSTEM_CONFIGURED,
                source="skill_evolution",
                data={
                    "type": improvement.type,
                    "target": improvement.target,
                    "action": improvement.action,
                    "success": success,
                    "error": error,
                },
            ))
        except Exception:
            pass

    def _log_audit(self, report: AuditReport) -> None:
        """Persist audit results to genome storage."""
        try:
            from gogeta.genome.storage import GenomeStorage
            storage = GenomeStorage()
            storage.add_evolution_entry({
                "event": "evolution_audit",
                "timestamp": time.time(),
                "improvements": len(report.improvements),
                "bottlenecks": len(report.bottlenecks),
                "deployed": report.deployed_count,
                "summary": report.summary,
            })
        except Exception:
            pass

    # ── Properties ───────────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "run_count": self._run_count,
            "deploy_enabled": self._deploy_enabled,
            "interval_days": DEFAULT_AUDIT_INTERVAL_DAYS,
            "last_report": self._last_report.to_dict() if self._last_report else None,
        }
