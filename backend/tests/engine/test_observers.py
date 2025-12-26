"""
Tests for Engine Observers

Unit tests for the Observer pattern implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.engine.observers.base import BaseObserver, ObserverManager
from app.engine.observers.event_types import (
    TokenEvent,
    NodeActiveEvent,
    NodeFinishedEvent,
    ToolStartEvent,
    ToolEndEvent,
    TokenUsageEvent,
    InterruptEvent,
    ErrorEvent,
)


class TestEventTypes:
    """Test event type creation and defaults."""
    
    def test_token_event(self):
        event = TokenEvent(content="Hello", node_id="agent_1")
        assert event.type == "token"
        assert event.content == "Hello"
        assert event.node_id == "agent_1"
        assert event.timestamp is not None
    
    def test_node_active_event(self):
        event = NodeActiveEvent(node_id="agent_1", node_name="Agent")
        assert event.type == "node_active"
        assert event.node_name == "Agent"
    
    def test_node_finished_event(self):
        event = NodeFinishedEvent(
            node_id="agent_1",
            output={"result": "done"},
            has_tool_calls=True
        )
        assert event.type == "node_finished"
        assert event.has_tool_calls is True
    
    def test_tool_events(self):
        start = ToolStartEvent(tool_name="search", tool_input={"query": "test"})
        assert start.type == "tool_start"
        
        end = ToolEndEvent(tool_name="search", tool_output="results")
        assert end.type == "tool_end"
    
    def test_token_usage_event(self):
        event = TokenUsageEvent(
            node_id="agent_1",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150
        )
        assert event.total_tokens == 150
    
    def test_error_event(self):
        event = ErrorEvent(message="Something failed", error_code="E001")
        assert event.type == "error"
        assert event.recoverable is False


class MockObserver(BaseObserver):
    """Test observer that tracks received events."""
    
    def __init__(self):
        self.events = []
    
    async def on_token(self, event: TokenEvent) -> None:
        self.events.append(("token", event))
    
    async def on_node_active(self, event: NodeActiveEvent) -> None:
        self.events.append(("node_active", event))
    
    async def on_error(self, event: ErrorEvent) -> None:
        self.events.append(("error", event))


class FailingObserver(BaseObserver):
    """Observer that raises on every event."""
    
    async def on_token(self, event: TokenEvent) -> None:
        raise RuntimeError("Observer failed")


class TestObserverManager:
    """Test observer registration and dispatch."""
    
    def test_register_observer(self):
        manager = ObserverManager()
        observer = MockObserver()
        
        manager.register(observer)
        assert manager.observer_count == 1
        
        # No duplicate registration
        manager.register(observer)
        assert manager.observer_count == 1
    
    def test_unregister_observer(self):
        manager = ObserverManager()
        observer = MockObserver()
        
        manager.register(observer)
        manager.unregister(observer)
        assert manager.observer_count == 0
    
    @pytest.mark.asyncio
    async def test_notify_single_observer(self):
        manager = ObserverManager()
        observer = MockObserver()
        manager.register(observer)
        
        event = TokenEvent(content="Hello")
        await manager.notify(event)
        
        assert len(observer.events) == 1
        assert observer.events[0][0] == "token"
    
    @pytest.mark.asyncio
    async def test_notify_multiple_observers(self):
        manager = ObserverManager()
        obs1 = MockObserver()
        obs2 = MockObserver()
        
        manager.register(obs1)
        manager.register(obs2)
        
        await manager.notify(TokenEvent(content="Test"))
        
        assert len(obs1.events) == 1
        assert len(obs2.events) == 1
    
    @pytest.mark.asyncio
    async def test_error_isolation(self):
        """One failing observer doesn't affect others."""
        manager = ObserverManager()
        failing = FailingObserver()
        working = MockObserver()
        
        manager.register(failing)
        manager.register(working)
        
        await manager.notify(TokenEvent(content="Test"))
        
        # Working observer still gets the event
        assert len(working.events) == 1
    
    def test_clear_observers(self):
        manager = ObserverManager()
        manager.register(MockObserver())
        manager.register(MockObserver())
        
        manager.clear()
        assert manager.observer_count == 0
