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

def make_serializable(obj: Any) -> Any:
    """
    Ensures an object is JSON serializable for WebSocket transmission.
    Handles Pydantic models, LangChain messages, and generic objects.
    """
    if hasattr(obj, "content"): return obj.content
    if hasattr(obj, "dict"): return obj.dict()
    try:
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError):
        return str(obj)
