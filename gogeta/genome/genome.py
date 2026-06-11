"""GenomeManager — Gogeta's experience-to-behaviour learning system.

Orchestrates workflow discovery, pattern detection, skill evolution,
failure learning, and genome report generation.

Usage::

    from gogeta.genome import GenomeManager
    gm = GenomeManager()
    gm.learn()           # run full discovery pipeline
    gm.report()          # write genome.md
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .confidence import confidence_label
from .evolution import learn_from_failures
from .graph import build_graph_json
from .patterns import detect_patterns
from .skills import evolve_skills
from .storage import GenomeStorage
from .workflows import discover_workflows

logger = logging.getLogger(__name__)


class GenomeManager:
    """Top-level orchestrator for the genome learning pipeline."""

    def __init__(
        self,
        genome_dir: Optional[Path] = None,
        analytics_store=None,
    ):
        self._storage = GenomeStorage(genome_dir)
        self._analytics = analytics_store
        self._lifeline_dir = Path.cwd() / "gogeta" / "lifeline"
        self._genome_dir = self._storage._dir

    @property
    def storage(self) -> GenomeStorage:
        return self._storage

    # ── Learning pipeline ────────────────────────────────────────────

    def learn(self, force: bool = False) -> Dict[str, int]:
        """Run the full genome learning pipeline.

        Returns a summary dict with counts of what was learned.
        """
        stats: Dict[str, int] = {}

        if self._analytics is None:
            logger.warning("No analytics store — skipping workflow discovery")
            return stats

        # 1. Discover workflows from tool_relationships
        workflows = discover_workflows(self._analytics)
        self._storage.save_workflows(workflows)
        stats["workflows"] = len(workflows)
        logger.info("Discovered %d workflows", len(workflows))

        # 2. Detect patterns from recent calls
        patterns = detect_patterns(self._analytics)
        self._storage.save_patterns(patterns)
        stats["patterns"] = len(patterns)
        logger.info("Detected %d patterns", len(patterns))

        # 3. Evolve skills from workflows + patterns
        new_skills = evolve_skills(self._storage, workflows, patterns)
        stats["new_skills"] = len(new_skills)
        logger.info("Evolved %d new skills", len(new_skills))

        # 4. Learn rules from failures
        new_rules = learn_from_failures(
            self._storage, self._lifeline_dir / "FAILURES.md",
        )
        stats["new_rules"] = len(new_rules)
        logger.info("Learned %d rules from failures", len(new_rules))

        # 5. Build workflow graph
        build_graph_json(self._storage)
        stats["graph_built"] = 1

        self._storage.add_evolution_entry({
            "action": "full_learn",
            "stats": stats,
        })

        return stats

    # ── Report ───────────────────────────────────────────────────────

    def report(self, output_path: Optional[Path] = None) -> str:
        """Generate genome.md — a markdown summary of learned knowledge."""
        if output_path is None:
            output_path = self._genome_dir / "genome.md"

        data = self._storage.get_report_data()
        workflows = data.get("workflows", [])
        patterns = data.get("patterns", [])
        skills = data.get("skills", [])
        rules = data.get("rules", [])
        evolution_log = data.get("evolution_log", [])
        updated = datetime.fromtimestamp(data.get("updated_at", 0))

        trusted_wf = [w for w in workflows if w.get("confidence", 0) >= 0.85]
        verified_wf = [w for w in workflows if 0.60 <= w.get("confidence", 0) < 0.85]
        trusted_pat = [p for p in patterns if p.get("confidence", 0) >= 0.85]
        trusted_skills = [s for s in skills if s.get("confidence", 0) >= 0.60]

        lines = [
            "# Gogeta Genome",
            "",
            f"*Generated: {updated.strftime('%Y-%m-%d %H:%M')}*",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Workflows | {len(workflows)} |",
            f"| Patterns | {len(patterns)} |",
            f"| Skills | {len(skills)} |",
            f"| Rules | {len(rules)} |",
            f"| Evolution Events | {len(evolution_log)} |",
            "",
            "---",
            "",
            "## Top Skills",
            "",
        ]

        if trusted_skills:
            for s in trusted_skills[:10]:
                conf_pct = int(s.get("confidence", 0) * 100)
                lines.append(f"1. **{s['display_name']}** — confidence {conf_pct}%")
        else:
            lines.append("*No trusted skills yet. More data needed.*")
        lines.append("")

        lines.extend([
            "---",
            "",
            "## Trusted Workflows",
            "",
        ])
        if trusted_wf:
            for wf in trusted_wf:
                steps = " -> ".join(wf.get("steps", []))
                lines.append(f"- **{wf.get('name', 'Workflow')}**: `{steps}`")
        else:
            lines.append("*No trusted workflows yet.*")
        lines.append("")

        lines.extend([
            "---",
            "",
            "## Verified Workflows",
            "",
        ])
        if verified_wf:
            for wf in verified_wf:
                steps = " -> ".join(wf.get("steps", []))
                lines.append(f"- {wf.get('name', 'Workflow')}: `{steps}`")
        else:
            lines.append("*No verified workflows yet.*")
        lines.append("")

        lines.extend([
            "---",
            "",
            "## Trusted Patterns",
            "",
        ])
        if trusted_pat:
            for p in trusted_pat:
                seq = " -> ".join(p.get("sequence", []))
                lines.append(f"- **{p.get('name', 'Pattern')}**: `{seq}`")
        else:
            lines.append("*No trusted patterns yet.*")
        lines.append("")

        lines.extend([
            "---",
            "",
            "## Learned Rules",
            "",
        ])
        if rules:
            for r in rules:
                lines.append(f"- {r.get('rule', '')}")
        else:
            lines.append("*No rules learned yet.*")
        lines.append("")

        lines.extend([
            "---",
            "",
            "## All Workflows (by confidence)",
            "",
        ])
        if workflows:
            for wf in workflows:
                conf_pct = int(wf.get("confidence", 0) * 100)
                label = wf.get("label", "seed")
                steps = " -> ".join(wf.get("steps", []))
                lines.append(f"- [{label}] **{wf.get('name', 'Workflow')}** ({conf_pct}%): `{steps}`")
        lines.append("")

        content = "\n".join(lines)
        output_path.write_text(content, encoding="utf-8")
        logger.info("Genome report written to %s", output_path)
        return content

    # ── Utility ──────────────────────────────────────────────────────

    def get_top_skills(self, limit: int = 5) -> List[Dict]:
        """Return highest-confidence skills."""
        skills = self._storage.load_skills()
        skills.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        return skills[:limit]

    def get_stats(self) -> Dict:
        data = self._storage.get_report_data()
        return {
            "workflows": len(data.get("workflows", [])),
            "patterns": len(data.get("patterns", [])),
            "skills": len(data.get("skills", [])),
            "rules": len(data.get("rules", [])),
            "evolution_events": len(data.get("evolution_log", [])),
        }
