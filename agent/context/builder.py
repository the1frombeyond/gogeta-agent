"""Context builder — assembles the final context window from multiple sources.

Combines recent messages, anchored session summary, relevant memories,
genome workflows, learned rules, and project intelligence into a single
optimised context window.

Flow:

    1. Start with recent messages (protected tail)
    2. Insert anchored session summary (if compression has occurred)
    3. Inject relevant memories (ranked, top-k)
    4. Inject relevant workflows (ranked, top-k)
    5. Inject relevant rules (ranked, top-k)
    6. Add recent failures/decisions if relevant
    7. Compress if over budget
    8. Return assembled context
"""

import logging
from typing import Any, Dict, List, Optional

from .budget import TokenBudget
from .ranking import RelevanceRanker
from .retrieval import ContextRetrieval
from .summarizer import SessionSummarizer

logger = logging.getLogger(__name__)

# Format string for genome knowledge injection into system prompt
_GENOME_CONTEXT_TEMPLATE = """
## Learned Workflows
{workflows}

## Relevant Rules
{rules}

## Key Memories
{memories}
"""

# Token budget for genome/lifeline injection overhead
_MAX_INJECTION_TOKENS = 2000


class ContextBuilder:
    """Assembles the optimal context window from all available sources.

    Usage::

        builder = ContextBuilder()
        messages = builder.build(messages, system_prompt, focus_topic="fix bug")
    """

    def __init__(
        self,
        summarizer: Optional[SessionSummarizer] = None,
        retrieval: Optional[ContextRetrieval] = None,
        ranker: Optional[RelevanceRanker] = None,
        budget: Optional[TokenBudget] = None,
    ):
        self._summarizer = summarizer or SessionSummarizer()
        self._retrieval = retrieval or ContextRetrieval()
        self._ranker = ranker or RelevanceRanker()
        self._budget = budget or TokenBudget()
        self._last_keywords: List[str] = []

    @property
    def summarizer(self) -> SessionSummarizer:
        return self._summarizer

    @property
    def budget(self) -> TokenBudget:
        return self._budget

    # ── Keyword extraction ──────────────────────────────────────────

    def _extract_keywords(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract keywords from recent user messages for relevance ranking."""
        keywords: List[str] = []
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be",
                      "been", "being", "have", "has", "had", "do", "does",
                      "did", "will", "would", "could", "should", "may",
                      "might", "shall", "can", "need", "must", "to", "of",
                      "in", "for", "on", "with", "at", "by", "from", "as",
                      "into", "through", "during", "before", "after", "up",
                      "out", "off", "over", "under", "again", "further",
                      "then", "once", "here", "there", "when", "where", "why",
                      "how", "all", "each", "every", "both", "few", "more",
                      "most", "other", "some", "such", "no", "nor", "not",
                      "only", "own", "same", "so", "than", "too", "very",
                      "just", "about", "above", "down", "what", "which",
                      "who", "and", "but", "or", "if", "because", "until",
                      "while", "that", "this", "these", "those", "it", "its",
                      "i", "me", "my", "we", "our", "you", "your", "he",
                      "she", "they", "them", "their", "hi", "hello", "hey",
                      "thanks", "thank", "please", "yes", "no", "ok", "okay"}

        for msg in reversed(messages):
            if msg.get("role") == "user":
                text = str(msg.get("content", ""))
                words = text.lower().split()
                for w in words:
                    clean = w.strip(".,!?;:'\"()[]{}+=-_*&^%$#@~`<>/\\|")
                    if len(clean) > 3 and clean not in stop_words and clean.isalpha():
                        if clean not in keywords:
                            keywords.append(clean)
                    if len(keywords) >= 10:
                        break
            if len(keywords) >= 10:
                break

        self._last_keywords = keywords
        return keywords

    # ── Context assembly ────────────────────────────────────────────

    def build(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        focus_topic: Optional[str] = None,
        include_genome: bool = True,
        include_lifeline: bool = True,
        include_project: bool = True,
    ) -> List[Dict[str, Any]]:
        """Assemble the optimised context window.

        Parameters
        ----------
        messages:
            The conversation messages to build context from.
        system_prompt:
            Current system prompt (may be augmented with genome context).
        focus_topic:
            Optional topic to focus relevance ranking on.
        include_genome:
            Whether to inject genome workflows and rules.
        include_lifeline:
            Whether to inject lifeline memories, failures, decisions.
        include_project:
            Whether to inject project intelligence.

        Returns
        -------
        The assembled message list (system prompt is prepended as first message).
        """
        keywords = self._extract_keywords(messages)
        if focus_topic:
            topic_words = focus_topic.lower().split()
            for w in topic_words:
                if w not in keywords and len(w) > 2:
                    keywords.append(w)
                    if len(keywords) >= 10:
                        break

        augmented_prompt = system_prompt

        # 1. Inject session summary (if compression has occurred)
        summary = self._summarizer.read()
        has_compressed = "Session started" not in summary
        if has_compressed and include_lifeline:
            augmented_prompt += (
                "\n\n---\n## Session Summary\n" +
                summary[:1000]
            )

        # 2. Inject genome knowledge
        genome_context = self._build_genome_context(
            keywords, include_genome, include_lifeline,
        )
        if genome_context:
            summary_part = genome_context[:int(
                _MAX_INJECTION_TOKENS * _CHARS_PER_TOKEN
            )]
            augmented_prompt += "\n\n---\n" + summary_part

        # 3. Inject project intelligence
        if include_project:
            project_context = self._build_project_context()
            if project_context:
                augmented_prompt += "\n\n---\n" + project_context

        assembled = list(messages)
        if augmented_prompt:
            # Update the system message or insert one
            if assembled and assembled[0].get("role") == "system":
                assembled[0] = {"role": "system", "content": augmented_prompt}
            else:
                assembled.insert(0, {"role": "system", "content": augmented_prompt})

        return assembled

    def _build_genome_context(
        self,
        keywords: List[str],
        include_genome: bool,
        include_lifeline: bool,
    ) -> str:
        """Build genome/lifeline injection string."""
        parts = []

        if include_lifeline:
            memories = self._retrieval.get_relevant_memories(keywords, top_k=3)
            if memories:
                mem_lines = [f"- {m['fact']}" for m in memories]
                parts.append("## Relevant Memories")
                parts.extend(mem_lines)

            failures = self._retrieval.get_failures(limit=2)
            if failures:
                parts.append("## Recent Failures (learn from these)")
                for f in failures:
                    lesson = f.get("lesson", "")
                    parts.append(f"- {lesson}")

        if include_genome:
            workflows = self._retrieval.get_relevant_workflows(keywords, top_k=2)
            if workflows:
                parts.append("## Applicable Workflows")
                for w in workflows:
                    steps = " -> ".join(w.get("steps", []))
                    conf = int(w.get("confidence", 0) * 100)
                    parts.append(f"- {w.get('name', 'Workflow')} ({conf}%): {steps}")

            rules = self._retrieval.get_relevant_rules(keywords, top_k=2)
            if rules:
                parts.append("## Rules to Follow")
                for r in rules:
                    parts.append(f"- {r.get('rule', '')}")

        return "\n".join(parts)

    def _build_project_context(self) -> str:
        """Build project intelligence injection string."""
        parts = []

        project = self._retrieval.get_project_md()
        if project:
            parts.append("## Project Context")
            parts.append(project[:500])

        tasks = self._retrieval.get_tasks_md()
        if tasks:
            parts.append("## Current Tasks")
            parts.append(tasks[:500])

        decisions = self._retrieval.get_decision_log()
        if decisions:
            parts.append("## Recent Decisions")
            parts.append(decisions[:500])

        return "\n".join(parts)

    # ── System prompt injection ─────────────────────────────────────

    def _inject_into_system_prompt(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        focus_topic: Optional[str] = None,
    ) -> str:
        """Augment a system prompt with genome/lifeline context.

        Called from ``compress_context()`` after the base system prompt
        has been rebuilt.  Returns the augmented prompt string.
        """
        keywords = self._extract_keywords(messages)
        if focus_topic:
            topic_words = focus_topic.lower().split()
            for w in topic_words:
                if w not in keywords and len(w) > 2:
                    keywords.append(w)
                    if len(keywords) >= 10:
                        break

        augmented = system_prompt

        # 1. Anchored session summary (if compression has occurred)
        summary = self._summarizer.read()
        has_compressed = "Session started" not in summary
        if has_compressed:
            augmented += (
                "\n\n---\n## Session Summary\n" +
                summary[:1000]
            )

        # 2. Genome workflows + lifeline memories
        genome_part = self._build_genome_context(
            keywords, include_genome=True, include_lifeline=True,
        )
        if genome_part:
            chars_limit = _MAX_INJECTION_TOKENS * _CHARS_PER_TOKEN
            augmented += "\n\n---\n" + genome_part[:chars_limit]

        # 3. Project intelligence
        project_part = self._build_project_context()
        if project_part:
            augmented += "\n\n---\n" + project_part[:1500]

        return augmented

    # ── Utility ─────────────────────────────────────────────────────

    def get_budget_status(self) -> Dict[str, Any]:
        """Return current budget status for display."""
        return self._budget.get_status()

    def get_summary(self) -> str:
        """Return current session summary text."""
        return self._summarizer.read()


# Module-level constant
_CHARS_PER_TOKEN = 4
