import logging
from typing import Optional

from agent.auxiliary_client import call_llm

from tools.browser._config import _get_extraction_model
from tools.browser._state import SNAPSHOT_SUMMARIZE_THRESHOLD, logger

logger = logging.getLogger(__name__)


def _extract_relevant_content(snapshot_text: str, user_task: str | None = None) -> str:
    if user_task:
        extraction_prompt = (
            f"You are a content extractor for a browser automation agent.\n\n"
            f"The user's task is: {user_task}\n\n"
            f"Given the following page snapshot (accessibility tree representation), "
            f"extract and summarize the most relevant information for completing this task. Focus on:\n"
            f"1. Interactive elements (buttons, links, inputs) that might be needed\n"
            f"2. Text content relevant to the task (prices, descriptions, headings, important info)\n"
            f"3. Navigation structure if relevant\n\n"
            f"Keep ref IDs (like [ref=e5]) for interactive elements so the agent can use them.\n\n"
            f"Page Snapshot:\n{snapshot_text}\n\n"
            f"Provide a concise summary that preserves actionable information and relevant content."
        )
    else:
        extraction_prompt = (
            f"Summarize this page snapshot, preserving:\n"
            f"1. All interactive elements with their ref IDs (like [ref=e5])\n"
            f"2. Key text content and headings\n"
            f"3. Important information visible on the page\n\n"
            f"Page Snapshot:\n{snapshot_text}\n\n"
        )
    try:
        model = _get_extraction_model()
        if model:
            result = call_llm(
                messages=[{"role": "user", "content": extraction_prompt}],
                model=model,
                max_tokens=4096,
            )
            return result.get("content", "").strip() or snapshot_text
        return _truncate_snapshot(snapshot_text)
    except Exception as e:
        logger.warning("Content extraction failed, using truncated snapshot: %s", e)
        return _truncate_snapshot(snapshot_text)


def _truncate_snapshot(snapshot_text: str, max_chars: int = 8000) -> str:
    if len(snapshot_text) <= max_chars:
        return snapshot_text
    half = max_chars // 2
    start = snapshot_text[:half]
    end = snapshot_text[-half:]
    return f"{start}\n\n... [truncated: {len(snapshot_text) - max_chars} characters omitted] ...\n\n{end}"
