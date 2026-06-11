"""Confidence scoring for genome workflows, patterns, and skills.

All learned items carry a confidence score 0.0 – 1.0.

Thresholds:
    < 0.30  — seed / candidate (never auto-executed)
    0.30–0.60 — emerging (listed, not promoted)
    0.60–0.85 — verified (eligible for auto-suggest)
    > 0.85  — trusted (promoted to core skill)
"""

import math
from typing import Dict, Optional


PROMOTION_THRESHOLD = 0.85
VERIFIED_THRESHOLD = 0.60
EMERGING_THRESHOLD = 0.30


def compute_workflow_confidence(
    frequency: int,
    success_rate: float,
    chain_length: int = 0,
    recency_bonus: bool = False,
) -> float:
    """Score a workflow on frequency × success rate with diminishing returns.

    Parameters
    ----------
    frequency:
        How often this workflow has been observed.
    success_rate:
        Fraction of successful completions (0.0 – 1.0).
    chain_length:
        Number of steps in the workflow.  Longer chains get a
        slight bonus because they represent a more specific pattern.
    recency_bonus:
        Whether the workflow was seen recently (boosts confidence).
    """
    if frequency == 0:
        return 0.0

    freq_factor = 1.0 - math.exp(-frequency / 10.0)
    base = 0.3 + 0.7 * (freq_factor * success_rate)

    if chain_length >= 3:
        base = min(1.0, base + 0.05)

    if recency_bonus:
        base = min(1.0, base + 0.05)

    return round(base, 3)


def compute_pattern_confidence(
    occurrences: int,
    distinct_sessions: int,
    completeness: float = 1.0,
) -> float:
    """Score a detected pattern.

    Parameters
    ----------
    occurrences:
        Times this exact sequence appeared.
    distinct_sessions:
        How many different sessions it appeared in.
        Higher = more generalisable.
    completeness:
        How much of the surrounding context was captured (0.0 – 1.0).
    """
    if occurrences == 0:
        return 0.0
    occ = 1.0 - math.exp(-occurrences / 5.0)
    ses = min(1.0, distinct_sessions / 5.0)
    score = 0.3 + 0.7 * (0.5 * occ + 0.3 * ses + 0.2 * completeness)
    return round(score, 3)


def compute_skill_confidence(
    workflow_confidence: float,
    pattern_confidence: float,
    age_days: float = 0.0,
    decay_rate: float = 0.01,
) -> float:
    """Combine workflow + pattern confidence for a skill score.

    Decays slowly (1% per day) so old skills must be refreshed.
    """
    base = 0.5 * workflow_confidence + 0.5 * pattern_confidence
    decay = math.exp(-decay_rate * age_days)
    return round(base * decay, 3)


def confidence_label(score: float) -> str:
    """Human label for a confidence level."""
    if score >= PROMOTION_THRESHOLD:
        return "trusted"
    if score >= VERIFIED_THRESHOLD:
        return "verified"
    if score >= EMERGING_THRESHOLD:
        return "emerging"
    return "seed"


def should_promote(score: float) -> bool:
    """Whether the item should be promoted to the next level."""
    return score >= VERIFIED_THRESHOLD
