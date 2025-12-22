"""
Engine Commands - Base Classes

Command pattern for graph compilation operations.
Each node type has its own compilation command.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set, Callable
from langgraph.graph import StateGraph, END

from app.logging import get_logger

logger = get_logger(__name__)


class CompileContext:
    """
    Shared context for compilation commands.
    
    Holds state that needs to be passed between commands.
    """
    
    def __init__(
        self,
        workflow: StateGraph,
        node_map: Dict[str, Dict],
        subgraph_loader: Optional[Callable] = None,
        recursion_depth: int = 0,
        visited_flow_ids: Optional[Set[str]] = None,
        extra_tools_map: Optional[Dict[str, Set[str]]] = None
    ):
        self.workflow = workflow
        self.node_map = node_map
        self.subgraph_loader = subgraph_loader
        self.recursion_depth = recursion_depth
        self.visited_flow_ids = visited_flow_ids or set()
        self.extra_tools_map = extra_tools_map or {}
        
        # Track compiled nodes
        self.node_ids: Set[str] = set()
        self.interrupt_nodes: list = []


class BaseCompileCommand(ABC):
    """
    Abstract base class for node compilation commands.
    
    Each node type (agent, tool, iterator, subgraph, router, smart)
    has its own command implementation.
    """
    
    # Node types this command handles
    node_types: list[str] = []
    
    @abstractmethod
    def execute(
        self, 
        node_id: str, 
        node_data: Dict[str, Any], 
        context: CompileContext
    ) -> None:
        """
        Compile a single node and add it to the workflow.
        
        Args:
            node_id: Unique node identifier
            node_data: Node configuration data
            context: Shared compilation context
        """
        pass
    
    def can_handle(self, node_type: str) -> bool:
        """Check if this command can handle the given node type."""
        return node_type in self.node_types
