"""Unified event bus — decouple producers from consumers.

Every system in Gogeta emits typed ``Event`` instances through the
central ``event_bus`` singleton rather than calling each other directly.

Quick start::

    from core.events.bus import event_bus
    from core.events.events import EventType

    # Subscribe
    def on_tool_finished(event):
        print(event.data["name"])

    event_bus.subscribe(EventType.TOOL_FINISHED, on_tool_finished)

    # Emit
    event_bus.emit(EventType.TOOL_FINISHED, {"name": "read_file"})

    # Start default subscribers (analytics, cost tracking, ...)
    from core.events.subscribers import start_default_subscribers
    subs = start_default_subscribers()

    # Optional: persist all events for audit/replay
    from core.events.persistence import event_persistence
    event_persistence.start()
"""

from .bus import EventBus, event_bus
from .events import Event, EventType
from .middleware import EventMiddleware

__all__ = [
    "EventBus",
    "Event",
    "EventType",
    "EventMiddleware",
    "event_bus",
]
