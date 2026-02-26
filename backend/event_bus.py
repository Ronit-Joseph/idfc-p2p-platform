import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List

logger = logging.getLogger(__name__)


class Event:
    """Represents a domain event in the P2P platform."""

    def __init__(self, name: str, data: Dict[str, Any], source: str = "unknown"):
        self.name = name
        self.data = data
        self.source = source
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp,
        }


# Type alias for async event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """In-process async event bus with subscribe/publish pattern.

    Supports event names like:
        pr.created, pr.approved, po.issued, invoice.captured,
        invoice.matched, payment.released, gst.irn_generated, etc.

    All published events are logged to an internal audit list for traceability.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._event_log: List[Dict[str, Any]] = []

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register an async handler for a specific event name."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
        logger.info("Handler %s subscribed to event '%s'", handler.__name__, event_name)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        if event_name in self._subscribers:
            self._subscribers[event_name] = [
                h for h in self._subscribers[event_name] if h is not handler
            ]

    async def publish(self, event: Event) -> None:
        """Publish an event — dispatches to all registered handlers asynchronously.

        Each handler is invoked via asyncio.create_task so that a slow or
        failing handler does not block the publisher or other handlers.
        """
        # Record in the audit log
        self._event_log.append(event.to_dict())
        logger.info("Event published: %s (source=%s)", event.name, event.source)

        handlers = self._subscribers.get(event.name, [])
        for handler in handlers:
            asyncio.create_task(self._safe_invoke(handler, event))

    async def _safe_invoke(self, handler: EventHandler, event: Event) -> None:
        """Invoke a handler and catch exceptions so one failure doesn't propagate."""
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "Handler %s failed for event '%s'", handler.__name__, event.name
            )

    @property
    def event_log(self) -> List[Dict[str, Any]]:
        """Return a copy of the audit event log."""
        return list(self._event_log)

    def clear_log(self) -> None:
        """Clear the event log (useful in tests)."""
        self._event_log.clear()


# Singleton instance — import this wherever you need the event bus
event_bus = EventBus()
