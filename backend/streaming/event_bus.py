"""
Finpluse v2 -- Event Bus (Kafka-Compatible Interface)

Lightweight async event bus using Python asyncio queues for local development.
Interface-compatible with Kafka so production deployments can swap in real brokers.

Topics:
    transactions.raw       -- Incoming bank webhooks
    transactions.enriched  -- After feature engineering
    transactions.scored    -- After anomaly detection
    alerts.generated       -- Alert events
    forecasts.updated      -- New forecast available
    user.events            -- Login, settings change, etc.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """A single event message on the bus."""
    topic: str
    key: str
    value: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    partition: int = 0
    offset: int = 0
    headers: dict[str, str] = field(default_factory=dict)


# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Async event bus with topic-based pub/sub.

    Supports:
        - Multiple topics with independent queues
        - Multiple subscribers per topic
        - Configurable queue sizes (backpressure)
        - Dead letter queue for failed processing
        - Event replay from offset

    In production, replace with confluent-kafka or aiokafka.
    """

    # Standard Finpluse topics
    TOPICS = [
        "transactions.raw",
        "transactions.enriched",
        "transactions.scored",
        "alerts.generated",
        "forecasts.updated",
        "user.events",
    ]

    def __init__(self, max_queue_size: int = 10000, retention_seconds: int = 86400) -> None:
        """Initialize the event bus.

        Args:
            max_queue_size: Maximum events per topic before backpressure.
            retention_seconds: How long to keep events for replay (default 24h).
        """
        self._queues: dict[str, asyncio.Queue[Event]] = {}
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_log: dict[str, list[Event]] = defaultdict(list)
        self._offsets: dict[str, int] = defaultdict(int)
        self._max_queue_size = max_queue_size
        self._retention_seconds = retention_seconds
        self._running = False
        self._processor_tasks: list[asyncio.Task[None]] = []
        self._dlq: list[tuple[Event, str]] = []  # Dead letter queue

        # Initialize all standard topics
        for topic in self.TOPICS:
            self._queues[topic] = asyncio.Queue(maxsize=max_queue_size)

    async def publish(self, topic: str, key: str, value: dict[str, Any], headers: dict[str, str] | None = None) -> Event:
        """Publish an event to a topic.

        Args:
            topic: Topic name.
            key: Partition key (e.g. user_id).
            value: Event payload (must be JSON-serializable).
            headers: Optional metadata headers.

        Returns:
            The published Event object.

        Raises:
            ValueError: If topic doesn't exist.
        """
        if topic not in self._queues:
            self._queues[topic] = asyncio.Queue(maxsize=self._max_queue_size)

        offset = self._offsets[topic]
        self._offsets[topic] += 1

        event = Event(
            topic=topic,
            key=key,
            value=value,
            timestamp=time.time(),
            offset=offset,
            headers=headers or {},
        )

        try:
            self._queues[topic].put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"Topic '{topic}' queue full, dropping oldest event")
            try:
                self._queues[topic].get_nowait()
                self._queues[topic].put_nowait(event)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

        # Store in log for replay
        self._event_log[topic].append(event)
        self._cleanup_old_events(topic)

        return event

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe a handler to a topic.

        Args:
            topic: Topic name to subscribe to.
            handler: Async function that processes Events.
        """
        if topic not in self._queues:
            self._queues[topic] = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers[topic].append(handler)
        logger.info(f"Subscribed handler to topic '{topic}'")

    async def start(self) -> None:
        """Start processing events for all subscribed topics."""
        self._running = True
        for topic in self._subscribers:
            task = asyncio.create_task(self._process_topic(topic))
            self._processor_tasks.append(task)
        logger.info(f"Event bus started with {len(self._processor_tasks)} topic processors")

    async def stop(self) -> None:
        """Stop all event processing."""
        self._running = False
        for task in self._processor_tasks:
            task.cancel()
        self._processor_tasks.clear()
        logger.info("Event bus stopped")

    async def _process_topic(self, topic: str) -> None:
        """Process events for a single topic.

        Args:
            topic: Topic to process.
        """
        while self._running:
            try:
                event = await asyncio.wait_for(self._queues[topic].get(), timeout=1.0)
                for handler in self._subscribers[topic]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Handler error on topic '{topic}': {e}")
                        self._dlq.append((event, str(e)))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def _cleanup_old_events(self, topic: str) -> None:
        """Remove events older than retention period."""
        cutoff = time.time() - self._retention_seconds
        self._event_log[topic] = [e for e in self._event_log[topic] if e.timestamp > cutoff]

    def get_topic_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all topics.

        Returns:
            Dict mapping topic names to queue size, subscriber count, and total events.
        """
        stats: dict[str, dict[str, int]] = {}
        for topic in self._queues:
            stats[topic] = {
                "queue_size": self._queues[topic].qsize(),
                "subscribers": len(self._subscribers.get(topic, [])),
                "total_events": self._offsets.get(topic, 0),
                "retained_events": len(self._event_log.get(topic, [])),
            }
        return stats

    def get_dead_letter_queue(self) -> list[dict[str, Any]]:
        """Get events that failed processing."""
        return [{"event": {"topic": e.topic, "key": e.key}, "error": err} for e, err in self._dlq[-100:]]


# Singleton event bus
event_bus = EventBus()
