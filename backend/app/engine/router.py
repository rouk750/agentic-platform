import re
from typing import Dict, Any, Callable, List, Optional
from app.engine.state import GraphState
from langgraph.graph import END

def make_router(routes: List[Dict[str, Any]], handle_to_target: Dict[str, str], default_target: Optional[str] = None, source_label: str = "Router") -> Callable[[GraphState], str]:
    """
    Creates a router function for a node based on a list of route definitions.
    
    Args:
        routes: A list of dicts, e.g. [{"condition": "contains", "value": "foo", "target_handle": "route-1"}]
        handle_to_target: A mapping of handle IDs (from UI) to actual target Node IDs.
        default_target: The target Node ID to use if no condition is met.
        source_label: Human readable label of the source node.
    """
    def router(state: GraphState) -> str:
        messages = state.get("messages", [])
        context = state.get("context", {})

        # Default fallback if no messages and no context logic (though context logic might run without messages)
        # But for 'message' based routing we need messages.
        
        for route in routes:
            condition = route.get("condition")
            value = route.get("value", "")
            target_handle = route.get("target_handle")
            source = route.get("source", "message") # Default to message
            context_key = route.get("context_key", "")
            
            # Resolve target node from handle
            target_node = handle_to_target.get(target_handle)
            if not target_node:
                continue

            # Determine content validation source
            content_to_check = ""

            if source == "context":
                if context_key:
                    raw_val = context.get(context_key, "")
                    content_to_check = str(raw_val) if raw_val is not None else ""
                else:
                    continue
            else:
                # Message based
                if not messages:
                    print(f"DEBUG Router: No messages found to route on.")
                    continue
                last_message = messages[-1]
                if hasattr(last_message, "content"):
                    content_to_check = str(last_message.content)

            from app.engine.debug import print_debug

            # Logic Evaluation
            matched = False
            if condition == "contains":
                if value and value.lower() in content_to_check.lower():
                    matched = True
            elif condition == "equals":
                if value and value.lower() == content_to_check.lower():
                     matched = True
            elif condition == "starts_with":
                if value and content_to_check.lower().startswith(value.lower()):
                     matched = True
            
            if matched:
                print_debug(f"DEBUG ROUTER {source_label}", {
                    "Content": content_to_check[:100],
                    "Condition": f"{condition} '{value}'",
                    "Result": "MATCH",
                    "Target": target_node
                })
                return target_node
            elif condition == "regex":
                if value:
                    try:
                        if re.search(value, content_to_check, re.IGNORECASE):
                            return target_node
                    except re.error:
                        print(f"Invalid regex fallback: {value}")
                        continue
            
        return default_target if default_target else END

    return router
