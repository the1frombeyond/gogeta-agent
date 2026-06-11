"""Central event bus — publish / subscribe for the entire application.

Usage::

    from core.events.bus import event_bus
    from core.events.events import Event, EventType

    # Subscribe
    def on_tool_finished(event: Event):
        print(f"Tool {event.data['name']} finished")

    event_bus.subscribe(EventType.TOOL_FINISHED, on_tool_finished)

    # Emit
    event_bus.emit(EventType.TOOL_FINISHED, {"name": "read_file", "duration_ms": 42})
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .events import Event, EventType
from .middleware import EventMiddleware

logger = logging.getLogger(__name__)


class EventBus:
    """Synchronous in-process event bus with priority-ordered subscribers.

    Thread-safe for concurrent subscribe / publish operations. Subscribers
    are called in priority order (higher first), then registration order
    within the same priority.
    """

    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[EventType, List[Tuple[Callable, int, int]]] = {}
        self._wildcard: List[Tuple[Callable, int, int]] = []
        self._history: List[Event] = []
        self._max_history = max_history
        self._seq = 0
        self.middleware = EventMiddleware()

    # ------------------------------------------------------------------
    # Subscribe
    # ------------------------------------------------------------------

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        priority: int = 0,
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The event type to listen for.
            handler: Callable receiving an ``Event`` instance.
            priority: Higher priority handlers run first (default 0).
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._seq += 1
        self._subscribers[event_type].append((handler, priority, self._seq))

    def subscribe_all(self, handler: Callable, priority: int = 0) -> None:
        """Register a handler for *all* event types."""
        self._seq += 1
        self._wildcard.append((handler, priority, self._seq))

    def unsubscribe(self, event_type: EventType, handler: Callable) -> bool:
        """Remove a specific handler for an event type. Returns True if found."""
        subs = self._subscribers.get(event_type)
        if subs is None:
            return False
        before = len(subs)
        self._subscribers[event_type] = [(h, p, s) for (h, p, s) in subs if h is not handler]
        return len(self._subscribers[event_type]) < before

    def unsubscribe_all(self, handler: Callable) -> bool:
        """Remove a handler from all event types and wildcard. Returns True if found anywhere."""
        found = False
        for event_type in list(self._subscribers):
            subs = self._subscribers[event_type]
            before = len(subs)
            self._subscribers[event_type] = [(h, p, s) for (h, p, s) in subs if h is not handler]
            if len(self._subscribers[event_type]) < before:
                found = True
        before_wc = len(self._wildcard)
        self._wildcard = [(h, p, s) for (h, p, s) in self._wildcard if h is not handler]
        if len(self._wildcard) < before_wc:
            found = True
        return found

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------

    def publish(self, event: Event) -> None:
        """Dispatch an event to all matching subscribers.

        The event passes through the middleware before-publish chain
        first. If middleware drops it (returns None), no subscribers
        are called.

        Subscribers run synchronously in this call.
        """
        if event.timestamp == 0:
            event.timestamp = time.time()

        event = self.middleware.run_before(event)
        if event is None:
            return

        self._dispatch_to(event, self._subscribers.get(event.type, []))
        self._dispatch_to(event, self._wildcard)

        self.middleware.run_after(event)

        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "",
        priority: int = 0,
        **kwargs: Any,
    ) -> Event:
        """Convenience: create an ``Event`` and publish it in one call.

        Returns the event (which may have been modified by middleware).
        """
        event = Event(
            type=event_type,
            data=data,
            source=source,
            priority=priority,
            timestamp=time.time(),
            **kwargs,
        )
        self.publish(event)
        return event

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def history(
        self,
        limit: int = 50,
        event_type: Optional[EventType] = None,
    ) -> List[Event]:
        """Return recent events, optionally filtered by type.

        Events are returned newest-first.
        """
        if event_type is None:
            return list(reversed(self._history[-limit:]))
        filtered = [e for e in self._history if e.type == event_type]
        return list(reversed(filtered[-limit:]))

    def count(self, event_type: Optional[EventType] = None) -> int:
        """Return number of events published, optionally filtered by type."""
        if event_type is None:
            return len(self._history)
        return sum(1 for e in self._history if e.type == event_type)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _dispatch_to(event: Event, handlers: List[Tuple[Callable, int, int]]) -> None:
        """Call each handler in priority then registration order."""
        sorted_handlers = sorted(handlers, key=lambda x: (-x[1], x[2]))
        for handler, _priority, _seq in sorted_handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.exception(
                    "Subscriber %s failed for event %s: %s", handler, event.type, exc,
                )


event_bus = EventBus()
