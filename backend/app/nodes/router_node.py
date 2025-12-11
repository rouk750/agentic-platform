from typing import Any, Dict
from app.engine.state import GraphState

class RouterNode:
    def __init__(self, node_id: str, config: dict = None):
        self.node_id = node_id
        self.config = config or {}
        
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """
        The RouterNode itself doesn't 'change' the state in a functional way,
        but it serves as a checkpoint and a visual step.
        The actual branching logic is handled by the Edges (conditional_edges)
        which will read this node's configuration.
        """
        # We could log the decision process here if we wanted, 
        # but the routing happens *after* this node execution in LangGraph.
        return {"last_sender": self.node_id}
