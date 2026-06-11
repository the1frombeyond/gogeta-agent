"""Workflow discovery — builds multi-step workflows from tool_relationships.

Uses the existing analytics_store to find frequent tool -> tool transitions
and chains them into complete workflows.
"""

import logging
from typing import Dict, List, Optional

from .confidence import compute_workflow_confidence

logger = logging.getLogger(__name__)


def discover_workflows(
    analytics_store,
    min_frequency: int = 2,
    max_depth: int = 5,
    min_chain: int = 2,
) -> List[Dict]:
    """Scan tool_relationships and build chained workflows.

    Algorithm:
        1. Get all tool pairs from the analytics store.
        2. Build a directed graph (adjacency list) weighted by frequency.
        3. For each tool that has outgoing edges, walk the most probable
           path up to ``max_depth`` steps.
        4. Deduplicate near-identical chains and score them.

    Returns a list of workflow dicts sorted by confidence descending.
    """
    pairs = analytics_store.get_workflows(
        min_frequency=min_frequency, limit=200,
    )
    if not pairs:
        return []

    adj: Dict[str, List[Dict]] = {}
    for p in pairs:
        adj.setdefault(p["tool_a"], []).append(p)

    seen: set = set()
    workflows: List[Dict] = []

    for start in adj:
        chain = _walk_chain(adj, start, max_depth)
        key = " -> ".join(chain)
        if key in seen or len(chain) < min_chain:
            continue
        seen.add(key)

        freq = min(p["frequency"] for p in pairs if p["tool_a"] in chain)
        success = min(p["success_rate"] for p in pairs if p["tool_a"] in chain)
        confidence = compute_workflow_confidence(
            frequency=freq, success_rate=success, chain_length=len(chain),
        )
        workflows.append({
            "id": f"wf_{len(workflows) + 1}",
            "name": _name_workflow(chain),
            "steps": chain,
            "frequency": freq,
            "success_rate": round(success, 3),
            "confidence": confidence,
            "label": _confidence_label(confidence),
        })

    workflows.sort(key=lambda w: w["confidence"], reverse=True)
    for i, wf in enumerate(workflows):
        wf["id"] = f"wf_{i + 1}"
    return workflows


def _walk_chain(
    adj: Dict[str, List[Dict]],
    start: str,
    max_depth: int,
) -> List[str]:
    """Greedily follow highest-frequency edges from *start*."""
    chain = [start]
    current = start
    visited = {start}
    for _ in range(max_depth - 1):
        edges = adj.get(current, [])
        edges.sort(key=lambda e: e["frequency"], reverse=True)
        best = None
        for e in edges:
            if e["tool_b"] not in visited:
                best = e
                break
        if best is None:
            break
        visited.add(best["tool_b"])
        chain.append(best["tool_b"])
        current = best["tool_b"]
    return chain


_CATEGORIES: Dict[str, str] = {
    "search": "Search",
    "read": "Read",
    "write": "Write",
    "edit": "Edit",
    "patch": "Edit",
    "test": "Test",
    "run": "Execute",
    "deploy": "Deploy",
    "build": "Build",
    "install": "Setup",
    "config": "Configure",
    "list": "List",
    "get": "Fetch",
}


def _name_workflow(steps: List[str]) -> str:
    """Derive a human-readable name from a tool chain."""
    for tool in steps:
        for keyword, category in _CATEGORIES.items():
            if keyword in tool.lower():
                return f"{category} Workflow"
    return f"Multi-step ({steps[0]}…)"


def _confidence_label(c: float) -> str:
    if c >= 0.85:
        return "trusted"
    if c >= 0.60:
        return "verified"
    if c >= 0.30:
        return "emerging"
    return "seed"
