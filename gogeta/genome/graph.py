"""Workflow graph builder — produces workflow_graph.json for visualisation.

Converts the genome's workflows and edges into a D3-friendly JSON format.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .storage import GenomeStorage


def build_graph_json(
    storage: GenomeStorage,
    output_path: Optional[Path] = None,
) -> Dict:
    """Build a graph JSON file from all stored workflows.

    Returns the graph dict and optionally writes to ``workflow_graph.json``.
    """
    if output_path is None:
        output_path = storage._dir / "workflow_graph.json"

    workflows = storage.load_workflows()
    nodes: Dict[str, Dict] = {}
    edges: List[Dict] = []

    for wf in workflows:
        wf_id = wf.get("id", "unknown")
        steps = wf.get("steps", [])
        conf = wf.get("confidence", 0.0)

        for order, tool in enumerate(steps):
            if tool not in nodes:
                nodes[tool] = {
                    "id": tool,
                    "label": tool.replace("_", " ").title(),
                    "workflows": [],
                    "frequency": 0,
                }
            if wf_id not in nodes[tool]["workflows"]:
                nodes[tool]["workflows"].append(wf_id)
                nodes[tool]["frequency"] += 1

        for i in range(len(steps) - 1):
            a, b = steps[i], steps[i + 1]
            edges.append({
                "source": a,
                "target": b,
                "workflow_id": wf_id,
                "confidence": conf,
            })

    graph = {
        "nodes": list(nodes.values()),
        "edges": edges,
        "workflows": workflows,
    }

    output_path.write_text(
        json.dumps(graph, indent=2, default=str), encoding="utf-8",
    )
    return graph
