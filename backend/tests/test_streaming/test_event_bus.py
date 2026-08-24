"""Tests for the event bus."""
import asyncio
import pytest
from streaming.event_bus import EventBus, Event


@pytest.fixture
def bus():
    return EventBus(max_queue_size=100)


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_event(self, bus):
        event = await bus.publish("transactions.raw", "user-1", {"amount": -50})
        assert event.topic == "transactions.raw"
        assert event.key == "user-1"
        assert event.value["amount"] == -50
        assert event.offset == 0

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("transactions.raw", handler)
        await bus.start()
        await bus.publish("transactions.raw", "user-1", {"amount": -50})
        await asyncio.sleep(0.1)
        await bus.stop()

        assert len(received) == 1
        assert received[0].value["amount"] == -50

    def test_topic_stats(self, bus):
        stats = bus.get_topic_stats()
        assert "transactions.raw" in stats
        assert stats["transactions.raw"]["queue_size"] == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus):
        counts = {"a": 0, "b": 0}

        async def handler_a(event):
            counts["a"] += 1

        async def handler_b(event):
            counts["b"] += 1

        bus.subscribe("user.events", handler_a)
        bus.subscribe("user.events", handler_b)
        await bus.start()
        await bus.publish("user.events", "user-1", {"type": "login"})
        await asyncio.sleep(0.1)
        await bus.stop()

        assert counts["a"] == 1
        assert counts["b"] == 1
