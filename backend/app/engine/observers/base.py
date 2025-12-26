"""
Base Observer Classes

Abstract base class for observers and the manager for registering/notifying.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Type, Set
from app.logging import get_logger

from .event_types import (
    EngineEvent,
    TokenEvent,
    NodeActiveEvent,
    NodeFinishedEvent,
    ToolStartEvent,
    ToolEndEvent,
    TokenUsageEvent,
    InterruptEvent,
    ErrorEvent,
)

logger = get_logger(__name__)


class BaseObserver(ABC):
    """
    Abstract base class for engine event observers.
    
    Subclass and implement the on_* methods you care about.
    Default implementations do nothing (optional handlers).
    """
    
    async def on_token(self, event: TokenEvent) -> None:
        """Called for each LLM token streamed."""
        pass
    
    async def on_node_active(self, event: NodeActiveEvent) -> None:
        """Called when a node starts execution."""
        pass
    
    async def on_node_finished(self, event: NodeFinishedEvent) -> None:
        """Called when a node completes execution."""
        pass
    
    async def on_tool_start(self, event: ToolStartEvent) -> None:
        """Called when a tool starts execution."""
        pass
    
    async def on_tool_end(self, event: ToolEndEvent) -> None:
        """Called when a tool completes execution."""
        pass
    
    async def on_token_usage(self, event: TokenUsageEvent) -> None:
        """Called with token usage statistics."""
        pass
    
    async def on_interrupt(self, event: InterruptEvent) -> None:
        """Called when execution is paused for HITL."""
        pass
    
    async def on_error(self, event: ErrorEvent) -> None:
        """Called on execution errors."""
        pass


class ObserverManager:
    """
    Manages a collection of observers and dispatches events to them.
    
    Thread-safe event dispatch with error isolation per observer.
    """
    
    def __init__(self):
        self._observers: List[BaseObserver] = []
    
    def register(self, observer: BaseObserver) -> None:
        """Register an observer to receive events."""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug("observer_registered", observer_type=type(observer).__name__)
    
    def unregister(self, observer: BaseObserver) -> None:
        """Remove an observer from event notifications."""
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug("observer_unregistered", observer_type=type(observer).__name__)
    
    def clear(self) -> None:
        """Remove all observers."""
        self._observers.clear()
    
    async def notify(self, event: EngineEvent) -> None:
        """
        Dispatch an event to all registered observers.
        
        Errors in one observer don't affect others.
        """
        handler_name = self._get_handler_name(event)
        
        for observer in self._observers:
            handler = getattr(observer, handler_name, None)
            if handler:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(
                        "observer_error",
                        observer_type=type(observer).__name__,
                        event_type=type(event).__name__,
                        error=str(e)
                    )
    
    def _get_handler_name(self, event: EngineEvent) -> str:
        """Map event type to handler method name."""
        event_type_map = {
            TokenEvent: "on_token",
            NodeActiveEvent: "on_node_active",
            NodeFinishedEvent: "on_node_finished",
            ToolStartEvent: "on_tool_start",
            ToolEndEvent: "on_tool_end",
            TokenUsageEvent: "on_token_usage",
            InterruptEvent: "on_interrupt",
            ErrorEvent: "on_error",
        }
        return event_type_map.get(type(event), "on_event")
    
    @property
    def observer_count(self) -> int:
        """Number of registered observers."""
        return len(self._observers)
