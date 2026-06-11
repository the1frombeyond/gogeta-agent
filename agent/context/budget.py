"""Token budget manager — tracks and enforces token budgets per request.

Monitors context, response, and tool token usage and provides guidance
on what to include or exclude based on available budget.

Works alongside the existing ContextCompressor's threshold management.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Rough estimate: 1 token ≈ 4 characters for most models
_CHARS_PER_TOKEN = 4

# Default budgets (can be overridden per model)
_DEFAULT_CONTEXT_BUDGET = 128_000
_DEFAULT_RESPONSE_BUDGET = 4_096
_DEFAULT_TOOL_BUDGET = 2_048
_DEFAULT_RESERVE = 0.20  # 20% reserve for safety margin


class TokenBudget:
    """Tracks token budgets and provides allocation guidance.

    Usage::

        budget = TokenBudget(context_limit=128000, response_limit=4096)
        budget.estimate_message_tokens(messages)
        available = budget.available_context()
        can_include = budget.can_include(estimated_tokens)
    """

    def __init__(
        self,
        context_limit: int = _DEFAULT_CONTEXT_BUDGET,
        response_limit: int = _DEFAULT_RESPONSE_BUDGET,
        tool_limit: int = _DEFAULT_TOOL_BUDGET,
        reserve_ratio: float = _DEFAULT_RESERVE,
    ):
        self._context_limit = context_limit
        self._response_limit = response_limit
        self._tool_limit = tool_limit
        self._reserve_ratio = reserve_ratio
        self._used_context = 0
        self._used_response = 0
        self._used_tools = 0

    # ── Estimation ──────────────────────────────────────────────────

    @staticmethod
    def estimate_text_tokens(text: str) -> int:
        """Rough token count for a text string."""
        return len(text) // _CHARS_PER_TOKEN + 1

    def estimate_message_tokens(self, msg: Dict[str, Any]) -> int:
        """Estimate tokens for a single message."""
        total = 0
        content = msg.get("content", "")
        if isinstance(content, str):
            total += self.estimate_text_tokens(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    total += self.estimate_text_tokens(part.get("text", ""))
                    if part.get("type") in ("image_url", "input_image", "image"):
                        total += 1600
                elif isinstance(part, str):
                    total += self.estimate_text_tokens(part)
        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    fn = tc.get("function", {})
                    total += self.estimate_text_tokens(fn.get("arguments", ""))
        role_bonus = {"system": 5, "user": 2, "assistant": 2, "tool": 1}
        total += role_bonus.get(msg.get("role", ""), 2)
        return total

    @staticmethod
    def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
        """Estimate total tokens for a list of messages."""
        budget = TokenBudget()
        return sum(budget.estimate_message_tokens(m) for m in messages)

    # ── Budget tracking ─────────────────────────────────────────────

    def record_usage(self, prompt_tokens: int, completion_tokens: int, tool_tokens: int = 0) -> None:
        """Record actual usage after an API call."""
        self._used_context = prompt_tokens
        self._used_response = completion_tokens
        self._used_tools = tool_tokens

    def reset(self) -> None:
        """Reset tracked usage."""
        self._used_context = 0
        self._used_response = 0
        self._used_tools = 0

    # ── Budget queries ──────────────────────────────────────────────

    @property
    def context_limit(self) -> int:
        return self._context_limit

    @context_limit.setter
    def context_limit(self, value: int) -> None:
        self._context_limit = value

    @property
    def available_context(self) -> int:
        """Remaining context tokens before hitting the limit."""
        return max(0, self._context_limit - self._used_context)

    @property
    def available_response(self) -> int:
        """Remaining response tokens."""
        return max(0, self._response_limit - self._used_response)

    @property
    def safe_context_limit(self) -> int:
        """Context limit with reserve margin."""
        return int(self._context_limit * (1.0 - self._reserve_ratio))

    @property
    def usage_percent(self) -> float:
        """Percentage of context budget used (0.0 – 1.0)."""
        if self._context_limit == 0:
            return 0.0
        return min(1.0, self._used_context / self._context_limit)

    def can_include(self, estimated_tokens: int) -> bool:
        """Whether an item of ``estimated_tokens`` fits in the remaining budget."""
        return self.available_context >= estimated_tokens

    def should_compress(self, threshold_ratio: float = 0.75) -> bool:
        """Whether context usage exceeds the compression threshold."""
        return self.usage_percent >= threshold_ratio

    def get_status(self) -> Dict[str, Any]:
        """Return a status dict for display/logging."""
        return {
            "context_limit": self._context_limit,
            "used_context": self._used_context,
            "available_context": self.available_context,
            "usage_percent": round(self.usage_percent * 100, 1),
            "response_limit": self._response_limit,
            "used_response": self._used_response,
        }
