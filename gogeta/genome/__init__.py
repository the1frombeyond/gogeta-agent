"""Genome — Gogeta's experience-to-behaviour learning system.

Turns raw tool analytics, failure logs, and session history into
reusable workflows, patterns, skills, and rules.

Files:
    genome.json         — learned workflows, patterns, skills, rules
    genome.db           — workflow graph edges (SQLite)
    genome.md           — human-readable report
    workflow_graph.json — D3-friendly graph data
    REFLECTIONS/        — auto-generated reflection entries
"""

from .genome import GenomeManager

__all__ = ["GenomeManager"]
