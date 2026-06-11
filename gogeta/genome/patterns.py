"""Pattern detection — finds repeated tool sequences from recent calls.

Scans the raw tool call history for n-gram patterns (sequences of 2–5 tools).
"""

import logging
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from .confidence import compute_pattern_confidence

logger = logging.getLogger(__name__)


def detect_patterns(
    analytics_store,
    min_occurrences: int = 2,
    ngram_sizes: Tuple[int, ...] = (2, 3, 4),
    recent_limit: int = 500,
) -> List[Dict]:
    """Scan recent tool calls and extract repeated sequences.

    Returns sorted list of pattern dicts, highest confidence first.
    """
    calls = analytics_store.get_recent_calls(limit=recent_limit)
    if not calls:
        return []

    calls.reverse()
    tool_names = [c.get("tool_name", "") for c in calls]
    sessions = [c.get("session_id", "") for c in calls]

    ngram_counter: Dict[Tuple[str, ...], int] = Counter()
    ngram_sessions: Dict[Tuple[str, ...], set] = defaultdict(set)

    for n in ngram_sizes:
        for i in range(len(tool_names) - n + 1):
            seq = tuple(tool_names[i:i + n])
            if all(t for t in seq):
                ngram_counter[seq] += 1
                ngram_sessions[seq].add(sessions[i] if i < len(sessions) else "")

    patterns: List[Dict] = []
    for seq, count in ngram_counter.most_common(50):
        if count < min_occurrences:
            continue
        session_count = len(ngram_sessions[seq])
        conf = compute_pattern_confidence(
            occurrences=count,
            distinct_sessions=session_count,
        )
        patterns.append({
            "sequence": list(seq),
            "occurrences": count,
            "sessions": session_count,
            "confidence": conf,
            "label": _confidence_label(conf),
            "name": _name_pattern(seq),
        })

    patterns.sort(key=lambda p: p["confidence"], reverse=True)
    return patterns


_PATTERN_NAMES: Dict[Tuple[str, ...], str] = {
    ("read_file", "grep", "edit_file"): "Fix in file",
    ("read_file", "grep", "edit_file", "run_tests"): "Bug Fix",
    ("edit_file", "run_tests", "edit_file", "run_tests"): "Iterative Fix",
    ("read_file", "read_file", "edit_file"): "Investigate & Edit",
    ("grep", "read_file", "edit_file"): "Search-Fix",
    ("run_tests", "read_file", "edit_file", "run_tests"): "Test-Driven Fix",
    ("edit_file", "run_tests"): "Edit & Test",
    ("read_file", "edit_file"): "Read & Edit",
    ("grep", "read_file"): "Search & Read",
    ("run_tests", "edit_file"): "Test-led Edit",
}


def _name_pattern(seq: Tuple[str, ...]) -> str:
    if len(seq) >= 2:
        key = tuple(seq[:min(len(seq), 4)])
        if key in _PATTERN_NAMES:
            return _PATTERN_NAMES[key]
    first = seq[0].replace("_", " ").title()
    last = seq[-1].replace("_", " ").title()
    if len(seq) == 2:
        return f"{first} + {last}"
    return f"{first} -> {last} ({len(seq)} steps)"


def _confidence_label(c: float) -> str:
    if c >= 0.85:
        return "trusted"
    if c >= 0.60:
        return "verified"
    if c >= 0.30:
        return "emerging"
    return "seed"
