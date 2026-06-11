"""Event middleware pipeline.

Middleware hooks run before (*before publish*) and after (*after publish*)
every event is dispatched to subscribers. Use them for cross-cutting
concerns like logging, filtering, enrichment, or telemetry.

A *before publish* hook can return ``None`` to drop the event.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from .events import Event

logger = logging.getLogger(__name__)

BeforePublishHook = Callable[[Event], Optional[Event]]
AfterPublishHook = Callable[[Event], None]


class EventMiddleware:
    """Ordered chain of before/after publish hooks."""

    def __init__(self):
        self._before: List[BeforePublishHook] = []
        self._after: List[AfterPublishHook] = []

    def register_before(self, hook: BeforePublishHook) -> None:
        """Register a hook that runs *before* subscribers are called.

        The hook receives the event and returns either the (possibly
        modified) event, or ``None`` to drop it entirely.
        """
        self._before.append(hook)

    def register_after(self, hook: AfterPublishHook) -> None:
        """Register a hook that runs *after* all subscribers have been called."""
        self._after.append(hook)

    def run_before(self, event: Event) -> Optional[Event]:
        """Run the before-publish chain. Returns the event or None if dropped."""
        for hook in self._before:
            try:
                result = hook(event)
                if result is None:
                    logger.debug("Event %s dropped by middleware %s", event.type, hook)
                    return None
                event = result
            except Exception as exc:
                logger.warning("Middleware hook %s failed: %s", hook, exc)
        return event

    def run_after(self, event: Event) -> None:
        """Run the after-publish chain."""
        for hook in self._after:
            try:
                hook(event)
            except Exception as exc:
                logger.warning("Middleware after-hook %s failed: %s", hook, exc)
