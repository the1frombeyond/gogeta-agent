"""Gogeta context engine — intelligent context assembly.

Subsystem that sits on top of the existing Gogeta ContextCompressor and adds
Gogeta-native features:

- Anchored session summaries (SESSION_SUMMARY.md, persisted to disk)
- Relevance ranking of messages and knowledge items
- Genome-aware context retrieval
- Token budget management
- Multi-source context builder

Usage::

    from agent.context import ContextBuilder, TokenBudget, RelevanceRanker
    builder = ContextBuilder()
    messages = builder.build(messages, system_prompt, genome, lifeline)
"""

from .budget import TokenBudget
from .builder import ContextBuilder
from .ranking import RelevanceRanker
from .retrieval import ContextRetrieval
from .summarizer import SessionSummarizer

__all__ = [
    "ContextBuilder",
    "ContextRetrieval",
    "RelevanceRanker",
    "SessionSummarizer",
    "TokenBudget",
]
