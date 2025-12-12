from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}

def overwrite_reducer(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """
    Reducer that favors the new value (b) over the old (a).
    Used to resolve concurrent updates to single-value keys.
    """
    return b if b is not None else a

class GraphState(TypedDict):
    """
    Represents the state of our graph.
    
    Attributes:
        messages: A list of messages that accumulates over time (reducer=add_messages).
        context: A shared memory blackboard for global variables.
        last_sender: The ID of the node that sent the last message.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    context: Annotated[Dict[str, Any], merge_dicts]
    last_sender: Annotated[Optional[str], overwrite_reducer]
