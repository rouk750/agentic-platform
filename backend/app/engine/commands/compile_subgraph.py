"""
Compile Command for Subgraph Nodes

Handles compilation of 'subgraph' type nodes.
"""

from typing import Dict, Any
import json

from app.engine.commands.base import BaseCompileCommand, CompileContext
from app.logging import get_logger
from app.exceptions import GraphCompilationError, CyclicDependencyError

logger = get_logger(__name__)


class CompileSubgraphCommand(BaseCompileCommand):
    """
    Compiles Subgraph nodes into the workflow.
    
    Subgraph nodes embed another flow as a nested graph.
    Handles cycle detection and recursion depth limits.
    """
    
    node_types = ["subgraph"]
    
    def execute(
        self, 
        node_id: str, 
        node_data: Dict[str, Any], 
        context: CompileContext
    ) -> None:
        """
        Compile a subgraph node.
        
        Args:
            node_id: Unique node identifier
            node_data: Subgraph configuration (flow_id or inline data)
            context: Shared compilation context
            
        Raises:
            GraphCompilationError: If subgraph_loader not provided
            CyclicDependencyError: If circular reference detected
        """
        if not context.subgraph_loader:
            raise GraphCompilationError(
                "Subgraph nodes require a subgraph_loader function",
                node_id=node_id,
                node_type="subgraph"
            )
        
        # Get the flow ID to load
        flow_id = node_data.get('flow_id') or node_data.get('subgraph_id')
        
        if not flow_id:
            raise GraphCompilationError(
                "Subgraph node missing flow_id",
                node_id=node_id,
                node_type="subgraph"
            )
        
        # Cycle detection
        if str(flow_id) in context.visited_flow_ids:
            raise CyclicDependencyError(flow_id=str(flow_id))
        
        # Load and compile subgraph
        try:
            subgraph_data = context.subgraph_loader(flow_id)
            
            if isinstance(subgraph_data, str):
                subgraph_data = json.loads(subgraph_data)
            
            # Import here to avoid circular dependency
            from app.engine.compiler import compile_graph
            
            # Track visited flows for cycle detection
            new_visited = context.visited_flow_ids.copy()
            new_visited.add(str(flow_id))
            
            subgraph = compile_graph(
                subgraph_data,
                checkpointer=None,
                subgraph_loader=context.subgraph_loader,
                recursion_depth=context.recursion_depth + 1,
                visited_flow_ids=new_visited
            )
            
            context.workflow.add_node(node_id, subgraph)
            context.node_ids.add(node_id)
            
            logger.debug("subgraph_compiled", node_id=node_id, flow_id=flow_id)
            
        except Exception as e:
            logger.error("subgraph_compilation_failed", node_id=node_id, flow_id=flow_id, error=str(e))
            raise GraphCompilationError(
                f"Failed to compile subgraph: {e}",
                node_id=node_id,
                node_type="subgraph",
                cause=e
            )
