"""
WebSocket Observer

Concrete observer that sends events to a WebSocket client.
"""

from fastapi import WebSocket
from typing import Optional

from .base import BaseObserver
from .event_types import (
    TokenEvent,
    NodeActiveEvent,
    NodeFinishedEvent,
    ToolStartEvent,
    ToolEndEvent,
    TokenUsageEvent,
    InterruptEvent,
    ErrorEvent,
)


class WebSocketObserver(BaseObserver):
    """
    Observer that forwards engine events to a WebSocket connection.
    
    Translates typed events to JSON format expected by frontend.
    """
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
    
    async def on_token(self, event: TokenEvent) -> None:
        """Send token to frontend for real-time display."""
        await self.websocket.send_json({
            "type": "token",
            "content": event.content,
            "node_id": event.node_id
        })
    
    async def on_node_active(self, event: NodeActiveEvent) -> None:
        """Notify frontend a node has started."""
        await self.websocket.send_json({
            "type": "node_active",
            "node_id": event.node_id,
            "node_name": event.node_name
        })
    
    async def on_node_finished(self, event: NodeFinishedEvent) -> None:
        """Notify frontend a node has completed."""
        await self.websocket.send_json({
            "type": "node_finished",
            "node_id": event.node_id,
            "node_name": event.node_name,
            "output": event.output,
            "has_tool_calls": event.has_tool_calls
        })
    
    async def on_tool_start(self, event: ToolStartEvent) -> None:
        """Notify frontend a tool is executing."""
        await self.websocket.send_json({
            "type": "tool_start",
            "node_id": event.node_id,
            "tool_name": event.tool_name,
            "tool_input": event.tool_input
        })
    
    async def on_tool_end(self, event: ToolEndEvent) -> None:
        """Notify frontend tool execution completed."""
        await self.websocket.send_json({
            "type": "tool_end",
            "node_id": event.node_id,
            "tool_name": event.tool_name,
            "tool_output": event.tool_output
        })
    
    async def on_token_usage(self, event: TokenUsageEvent) -> None:
        """Send token usage statistics."""
        await self.websocket.send_json({
            "type": "token_usage",
            "node_id": event.node_id,
            "usage": {
                "input_tokens": event.input_tokens,
                "output_tokens": event.output_tokens,
                "total_tokens": event.total_tokens
            }
        })
    
    async def on_interrupt(self, event: InterruptEvent) -> None:
        """Notify frontend execution is paused."""
        await self.websocket.send_json({
            "type": "interrupt",
            "node_id": event.node_id,
            "pending_tools": event.pending_tools
        })
    
    async def on_error(self, event: ErrorEvent) -> None:
        """Send error to frontend."""
        await self.websocket.send_json({
            "type": "error",
            "message": event.message,
            "node_id": event.node_id,
            "error_code": event.error_code,
            "recoverable": event.recoverable
        })
