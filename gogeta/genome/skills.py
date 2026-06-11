"""Skill evolution — converts high-confidence workflows and patterns into skills.

Skills are stored in genome.json and can be exported as SKILL.md files.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .confidence import compute_skill_confidence
from .storage import GenomeStorage

logger = logging.getLogger(__name__)


def evolve_skills(
    storage: GenomeStorage,
    workflows: List[Dict],
    patterns: List[Dict],
) -> List[Dict]:
    """Merge high-confidence workflows and patterns into skill definitions.

    A skill combines the best workflow + pattern for a common task,
    with a description, steps, and confidence score.
    """
    existing = {s["name"] for s in storage.load_skills()}
    new_skills: List[Dict] = []
    candidate_pool: List[Dict] = []

    for wf in workflows:
        if wf["confidence"] >= 0.50:
            candidate_pool.append({
                "source": "workflow",
                "name": wf.get("name", "Unnamed workflow"),
                "steps": wf.get("steps", []),
                "confidence": wf["confidence"],
            })

    for pat in patterns:
        if pat["confidence"] >= 0.50:
            candidate_pool.append({
                "source": "pattern",
                "name": pat.get("name", "Unnamed pattern"),
                "steps": pat.get("sequence", []),
                "confidence": pat["confidence"],
            })

    merged = _merge_candidates(candidate_pool)

    for item in merged:
        safe_name = item["name"].lower().replace(" ", "_").replace("/", "_")[:40]
        skill_name = f"{safe_name}_v1"
        if skill_name in existing:
            continue

        wf_conf = item.get("workflow_conf", 0.0)
        pat_conf = item.get("pattern_conf", 0.0)
        skill_conf = compute_skill_confidence(wf_conf, pat_conf)

        skill = {
            "name": skill_name,
            "display_name": item["name"],
            "description": _describe(item["steps"], item["name"]),
            "steps": item["steps"],
            "confidence": skill_conf,
            "label": _label(skill_conf),
            "source": item.get("source", "workflow"),
            "created_at": datetime.now().isoformat(),
            "executions": 0,
        }
        new_skills.append(skill)
        storage.save_workflow_graph(skill_name, item["steps"])
        storage.add_evolution_entry({
            "action": "skill_created",
            "name": skill_name,
            "confidence": skill_conf,
        })

    all_skills = storage.load_skills() + new_skills
    storage.save_skills(all_skills)
    return new_skills


def _merge_candidates(
    candidates: List[Dict],
) -> List[Dict]:
    """Deduplicate candidates that describe the same workflow."""
    seen: set = set()
    merged: List[Dict] = []
    for c in candidates:
        key = " -> ".join(c["steps"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(c)
    return merged


def _describe(steps: List[str], name: str) -> str:
    if not steps:
        return name
    return f"{name}: {' -> '.join(steps)}"


def _label(conf: float) -> str:
    if conf >= 0.85:
        return "trusted"
    if conf >= 0.60:
        return "verified"
    if conf >= 0.30:
        return "emerging"
    return "seed"
