"""Relevance ranking — scores messages and context items by importance.

Uses simple heuristic scoring (length, recency, tool activity, keyword
matches) to rank what should be preserved or included in the context window.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RelevanceRanker:
    """Scores items (messages, memories, workflows) by relevance.

    Higher score = more important to preserve.
    """

    def __init__(self):
        self._weights = {
            "has_tool_calls": 0.15,
            "has_error": 0.20,
            "is_user_message": 0.10,
            "is_recent": 0.15,
            "length_factor": 0.05,
            "keyword_match": 0.15,
            "has_code_block": 0.10,
            "from_lifeline": 0.05,
            "from_genome": 0.05,
        }

    def score_message(
        self,
        msg: Dict[str, Any],
        index: int,
        total: int,
        keywords: Optional[List[str]] = None,
    ) -> float:
        """Score a single conversation message.

        Parameters
        ----------
        msg:
            OpenAI-style message dict with ``role`` and ``content``.
        index:
            Position in the conversation (0 = first).
        total:
            Total messages in the conversation.
        keywords:
            Optional list of keywords to boost.
        """
        score = 0.0
        text = str(msg.get("content", ""))

        # System prompt always high priority
        if msg.get("role") == "system":
            score += 0.30

        # Recent messages get a bonus
        recency = index / max(total, 1)
        score += recency * self._weights["is_recent"]

        # User messages are generally more important
        if msg.get("role") == "user":
            score += self._weights["is_user_message"]

        # Tool calls indicate action
        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            score += self._weights["has_tool_calls"]

        # Errors are always important
        if "error" in text.lower() or "exception" in text.lower() or "traceback" in text.lower():
            score += self._weights["has_error"]

        # Code blocks indicate substantive content
        if "```" in text:
            score += self._weights["has_code_block"]

        # Length bonus (longer messages tend to have more content)
        if len(text) > 500:
            score += self._weights["length_factor"]

        # Keyword matches
        if keywords:
            text_lower = text.lower()
            for kw in keywords:
                if kw.lower() in text_lower:
                    score += self._weights["keyword_match"] / max(len(keywords), 1)

        return min(score, 1.0)

    def score_memory(self, memory: Dict[str, Any], keywords: Optional[List[str]] = None) -> float:
        """Score a memory item from Lifeline."""
        fact = memory.get("fact", "").lower()
        score = 0.0
        if keywords:
            for kw in keywords:
                if kw.lower() in fact:
                    score += 0.20
        if memory.get("category") in {"user", "preference", "important"}:
            score += 0.15
        return min(score, 1.0)

    def score_workflow(self, workflow: Dict[str, Any], keywords: Optional[List[str]] = None) -> float:
        """Score a genome workflow for relevance to current task."""
        name = workflow.get("name", "").lower()
        steps = " ".join(workflow.get("steps", [])).lower()
        combined = name + " " + steps
        score = workflow.get("confidence", 0.0) * 0.5
        if keywords:
            for kw in keywords:
                if kw.lower() in combined:
                    score += 0.15
        return min(score, 1.0)

    def score_rule(self, rule: Dict[str, Any], keywords: Optional[List[str]] = None) -> float:
        """Score a genome rule for relevance."""
        rule_text = rule.get("rule", "").lower()
        score = 0.0
        if keywords:
            for kw in keywords:
                if kw.lower() in rule_text:
                    score += 0.25
        if rule.get("source") == "failure":
            score += 0.10
        return min(score, 1.0)

    def rank_messages(
        self,
        messages: List[Dict[str, Any]],
        keywords: Optional[List[str]] = None,
        top_k: int = 0,
    ) -> List[Dict[str, Any]]:
        """Rank and optionally filter to top-k messages."""
        total = len(messages)
        scored = []
        for i, msg in enumerate(messages):
            s = self.score_message(msg, i, total, keywords)
            scored.append((s, msg))
        scored.sort(key=lambda x: x[0], reverse=True)
        if top_k > 0:
            scored = scored[:top_k]
        return [msg for _, msg in scored]

    def filter_top(
        self,
        items: List[Any],
        scorer,
        keywords: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Any]:
        """Generic filter: score items, return top-k above min_score."""
        scored = []
        for item in items:
            s = scorer(item, keywords)
            if s >= min_score:
                scored.append((s, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]
