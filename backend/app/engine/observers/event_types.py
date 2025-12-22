"""
Engine Event Types

Pydantic models for strongly-typed engine events.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class EngineEvent(BaseModel):
    """Base class for all engine events."""
    timestamp: datetime = None
    node_id: Optional[str] = None
    
    def __init__(self, **data):
        if data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class TokenEvent(EngineEvent):
    """LLM token streaming event."""
    type: str = "token"
    content: str


class NodeActiveEvent(EngineEvent):
    """Node execution started."""
    type: str = "node_active"
    node_name: Optional[str] = None


class NodeFinishedEvent(EngineEvent):
    """Node execution completed."""
    type: str = "node_finished"
    node_name: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    has_tool_calls: bool = False


class ToolStartEvent(EngineEvent):
    """Tool execution started."""
    type: str = "tool_start"
    tool_name: str
    tool_input: Optional[Dict[str, Any]] = None


class ToolEndEvent(EngineEvent):
    """Tool execution completed."""
    type: str = "tool_end"
    tool_name: str
    tool_output: Optional[str] = None


class TokenUsageEvent(EngineEvent):
    """Token usage statistics."""
    type: str = "token_usage"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class InterruptEvent(EngineEvent):
    """Execution paused for human-in-the-loop."""
    type: str = "interrupt"
    pending_tools: Optional[List[str]] = None


class ErrorEvent(EngineEvent):
    """Execution error."""
    type: str = "error"
    message: str
    error_code: Optional[str] = None
    recoverable: bool = False
