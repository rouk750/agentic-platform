from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


def smart_merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two dictionaries. 
    If a key exists in both and both values are lists, they are concatenated (Map-Reduce style).
    Otherwise, b overwrites a.
    """
    output = a.copy()
    for k, v in b.items():
        if k in output and isinstance(output[k], list) and isinstance(v, list):
            output[k] = output[k] + v
        else:
            output[k] = v
    return output

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
        context: A shared memory blackboard for global variables. (reducer=smart_merge_dicts)
        last_sender: The ID of the node that sent the last message.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    context: Annotated[Dict[str, Any], smart_merge_dicts]
    last_sender: Annotated[Optional[str], overwrite_reducer]
