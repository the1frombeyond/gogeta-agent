"""Knowledge Gap Detection — Law 1 of the Gogeta Autonomy Directive.

After every LLM response, a lightweight judge LLM assesses the output for
unsupported claims, guessed facts, or confident-sounding statements that may
be wrong. If gaps are found below the confidence threshold, the detector
automatically executes grounding tools and feeds results back to the model
before returning a final answer.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from core.events.bus import event_bus
from core.events.events import Event, EventType

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────

DEFAULT_CONFIDENCE_THRESHOLD = 0.8
"""Minimum confidence score required to skip research. Below this, the
detector triggers grounding tool execution."""

DEFAULT_MAX_RESEARCH_TOOLS = 3
"""Maximum number of grounding tools to invoke per gap-detection pass."""

KNOWLEDGE_GAP_SYSTEM_PROMPT = (
    "You are a fact-checking judge. Your job is to analyze the assistant's "
    "response and identify any claims that rely on knowledge the assistant "
    "could not be certain of — such as: current dates/times, recent events, "
    "specific numbers or statistics, availability of software packages or "
    "APIs, file paths or directory structures on the user's system, prices, "
    "or any fact that would require real-time verification.\n\n"
    'Return a JSON object with a single key "gaps" containing a list of gap '
    "objects, each with:\n"
    '  - "claim": the exact claim from the response\n'
    '  - "confidence": your confidence that the claim is correct (0.0 to 1.0)\n'
    '  - "reason": why this needs verification\n'
    '  - "suggested_tool": one of: "web_search", "fetch_url", "current_time", '
    '"check_package_version", "check_command", "resolve_path", "calculate", '
    '"dns_lookup", "system_info", "check_env_var"\n'
    '  - "query": the exact search query or parameter to pass to the tool\n\n'
    'If every claim in the response has high confidence (above 0.8), return '
    '{"gaps": []}. Do NOT add gaps for well-known facts or general knowledge.'
)


@dataclass
class KnowledgeGap:
    claim: str
    confidence: float
    reason: str
    suggested_tool: str
    query: str


@dataclass
class GapDetectionResult:
    gaps: List[KnowledgeGap] = field(default_factory=list)
    confidence_score: float = 1.0
    research_performed: bool = False
    research_results: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: Optional[str] = None


class KnowledgeGapDetector:
    """Detects and fills knowledge gaps in agent responses.

    Uses a lightweight LLM judge to assess each agent response. When gaps
    below the confidence threshold are found, executes grounding tools and
    returns structured research results that can be injected back into the
    conversation loop.
    """

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        max_research_tools: int = DEFAULT_MAX_RESEARCH_TOOLS,
        enabled: bool = True,
        call_llm: Optional[Callable] = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.max_research_tools = max_research_tools
        self.enabled = enabled
        self._call_llm = call_llm or self._default_call_llm
        self._research_count = 0
        self._total_gaps_found = 0

    def analyze(
        self,
        response: str,
        messages: List[Dict[str, Any]],
    ) -> GapDetectionResult:
        """Analyze a response for knowledge gaps.

        Args:
            response: The assistant's text response to evaluate.
            messages: The full conversation history (for context).

        Returns:
            GapDetectionResult with any detected gaps.
        """
        result = GapDetectionResult()
        if not self.enabled or not response.strip():
            return result

        start = time.monotonic()

        try:
            gaps = self._detect_gaps(response, messages)
        except Exception as exc:
            logger.warning("Knowledge gap detection failed: %s", exc)
            result.error = str(exc)
            return result

        if not gaps:
            result.elapsed_seconds = time.monotonic() - start
            return result

        self._total_gaps_found += len(gaps)
        result.gaps = gaps

        low_gaps = [g for g in gaps if g.confidence < self.confidence_threshold]
        if not low_gaps:
            result.confidence_score = min(g.confidence for g in gaps)
            result.elapsed_seconds = time.monotonic() - start
            return result

        result.confidence_score = min(g.confidence for g in low_gaps)

        self._research_count += 1
        result.research_performed = True

        tool_results = self._execute_research(low_gaps)
        result.research_results = tool_results

        event_bus.emit(Event(
            type=EventType.KNOWLEDGE_GAP_DETECTED,
            source="knowledge_gap_detector",
            data={
                "gap_count": len(gaps),
                "research_count": len(tool_results),
                "confidence": result.confidence_score,
                "research_performed": True,
            },
        ))

        result.elapsed_seconds = time.monotonic() - start
        return result

    def _detect_gaps(
        self,
        response: str,
        messages: List[Dict[str, Any]],
    ) -> List[KnowledgeGap]:
        """Use an LLM judge to find knowledge gaps in the response.

        Sends the response to a lightweight judge model, which returns
        structured gap data.
        """
        user_prompt = (
            "Analyze the following assistant response for knowledge gaps:\n\n"
            f"{response}"
        )

        judge_messages = [
            {"role": "system", "content": KNOWLEDGE_GAP_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        judge_response = self._call_llm(
            task="knowledge_gap",
            messages=judge_messages,
            temperature=0.0,
            max_tokens=2000,
        )

        raw = judge_response.choices[0].message.content or "{}"
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("\n", 1)[0] if "\n" in raw else raw
            raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Knowledge gap judge returned invalid JSON: %s", raw[:200])
            return []

        gaps_raw = parsed.get("gaps", [])
        if not isinstance(gaps_raw, list):
            return []

        gaps = []
        for g in gaps_raw:
            if not isinstance(g, dict):
                continue
            claim = g.get("claim", "")
            confidence = float(g.get("confidence", 1.0))
            reason = g.get("reason", "")
            suggested_tool = g.get("suggested_tool", "web_search")
            query = g.get("query", claim)
            if claim and confidence < 1.0:
                gaps.append(KnowledgeGap(
                    claim=claim,
                    confidence=confidence,
                    reason=reason,
                    suggested_tool=suggested_tool,
                    query=query,
                ))

        return gaps

    def _execute_research(
        self,
        gaps: List[KnowledgeGap],
    ) -> List[Dict[str, Any]]:
        """Run grounding tools to fill detected knowledge gaps.

        Deduplicates by tool+query, limits to max_research_tools calls.
        Returns list of {tool, query, result} dicts.
        """
        seen = set()
        results = []

        for gap in gaps:
            if len(results) >= self.max_research_tools:
                break

            key = (gap.suggested_tool, gap.query)
            if key in seen:
                continue
            seen.add(key)

            try:
                tool_fn = _GROUNDING_TOOL_MAP.get(gap.suggested_tool)
                if not tool_fn:
                    logger.debug("No handler for grounding tool %s", gap.suggested_tool)
                    continue
                tool_result = tool_fn(gap.query)
                results.append({
                    "tool": gap.suggested_tool,
                    "query": gap.query,
                    "claim": gap.claim,
                    "result": tool_result,
                })
            except Exception as exc:
                logger.warning(
                    "Grounding tool %s(%r) failed: %s",
                    gap.suggested_tool, gap.query, exc,
                )

        return results

    @staticmethod
    def _default_call_llm(**kwargs) -> Any:
        raise RuntimeError(
            "KnowledgeGapDetector requires a call_llm function. "
            "Pass one to __init__ or configure the auxiliary task."
        )

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "research_passes": self._research_count,
            "total_gaps_found": self._total_gaps_found,
            "confidence_threshold": self.confidence_threshold,
            "enabled": self.enabled,
        }


def build_research_context(results: List[Dict[str, Any]]) -> str:
    """Format research results into a context block for the model.

    Returns a string that can be prepended to the conversation as a
    tool-style result message.
    """
    if not results:
        return ""

    lines = [
        "━━━ Knowledge Gap Research Results ━━━",
        "The following facts were verified before answering:",
        "",
    ]
    for r in results:
        tool = r.get("tool", "?")
        query = r.get("query", "")
        claim = r.get("claim", "")
        result = r.get("result", {})
        output = ""
        if isinstance(result, dict):
            if result.get("success"):
                output = str(result.get("output", ""))
            else:
                output = f"Error: {result.get('error', 'unknown')}"
        lines.append(f"  Tool: {tool}")
        lines.append(f"  Query: {query}")
        lines.append(f"  Claim: {claim}")
        lines.append(f"  Result: {output[:500]}")
        lines.append("")

    return "\n".join(lines)


# ── Grounding tool adapter map ─────────────────────────────────────────

def _web_search_adapter(query: str) -> dict:
    from tools.grounding_tools import web_search
    return web_search(query=query)


def _current_time_adapter(query: str) -> dict:
    from tools.grounding_tools import current_time
    tz = query.strip() if query.strip() else "local"
    return current_time(timezone=tz)


def _fetch_url_adapter(query: str) -> dict:
    from tools.grounding_tools import fetch_url
    return fetch_url(url=query)


def _check_package_adapter(query: str) -> dict:
    from tools.grounding_tools import check_package_version
    return check_package_version(package_name=query)


def _check_command_adapter(query: str) -> dict:
    from tools.grounding_tools import check_command_exists
    return check_command_exists(command=query)


def _resolve_path_adapter(query: str) -> dict:
    from tools.grounding_tools import resolve_path
    return resolve_path(path=query)


def _calculate_adapter(query: str) -> dict:
    from tools.grounding_tools import calculate
    return calculate(expression=query)


def _dns_lookup_adapter(query: str) -> dict:
    from tools.grounding_tools import dns_lookup
    return dns_lookup(hostname=query)


def _system_info_adapter(query: str = "") -> dict:
    from tools.grounding_tools import system_info
    return system_info()


def _check_env_var_adapter(query: str) -> dict:
    from tools.grounding_tools import check_env_var
    return check_env_var(var_name=query)


_GROUNDING_TOOL_MAP: Dict[str, Any] = {
    "web_search": _web_search_adapter,
    "current_time": _current_time_adapter,
    "fetch_url": _fetch_url_adapter,
    "check_package_version": _check_package_adapter,
    "check_command": _check_command_adapter,
    "resolve_path": _resolve_path_adapter,
    "calculate": _calculate_adapter,
    "dns_lookup": _dns_lookup_adapter,
    "system_info": _system_info_adapter,
    "check_env_var": _check_env_var_adapter,
}
