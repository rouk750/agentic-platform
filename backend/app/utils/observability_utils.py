import json
from typing import Any, Optional, Dict

def extract_node_id(event: Dict[str, Any]) -> Optional[str]:
    """
    Extracts the LangGraph node ID from an event's tags or metadata.
    """
    tags = event.get("tags", [])
    node_id = None
    for tag in tags:
        if tag.startswith("langgraph:node:"):
            node_id = tag.split(":", 2)[2]
            break
            
    if not node_id and "metadata" in event and "langgraph_node" in event["metadata"]:
        node_id = event["metadata"]["langgraph_node"]
        
    return node_id

def make_serializable(obj: Any, max_string_length: int = 5000, max_depth: int = 5, current_depth: int = 0) -> Any:
    """
    Ensures an object is JSON serializable for WebSocket transmission.
    Handles Pydantic models, LangChain messages, and generic objects.
    Truncates large strings and deeply nested structures to prevent payload explosion.
    """
    if current_depth > max_depth:
        return "<Max Depth Exceeded>"

    # Handle Pydantic models
    if hasattr(obj, "dict"):
        # Pydantic v1
        return make_serializable(obj.dict(), max_string_length, max_depth, current_depth + 1)
    if hasattr(obj, "model_dump"):
         # Pydantic v2
        return make_serializable(obj.model_dump(), max_string_length, max_depth, current_depth + 1)
        
    # Handle LangChain Messages
    if hasattr(obj, "content"):
        return make_serializable(obj.content, max_string_length, max_depth, current_depth + 1)

    # Handle built-in collections
    if isinstance(obj, dict):
        return {
            str(k): make_serializable(v, max_string_length, max_depth, current_depth + 1)
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple, set)):
        return [
            make_serializable(item, max_string_length, max_depth, current_depth + 1) 
            for item in obj
        ]

    # Handle Strings with Truncation
    if isinstance(obj, str):
        if len(obj) > max_string_length:
            return obj[:max_string_length] + f"... <Truncated: {len(obj) - max_string_length} chars>"
        return obj

    # Handle other primitives
    if obj is None or isinstance(obj, (int, float, bool)):
        return obj

    # Fallback to string representation for unknown types
    try:
        # Check if it's already JSON safe (unlikely if we reached here for complex types)
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError):
        return str(obj)
