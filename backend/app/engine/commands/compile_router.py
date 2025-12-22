"""
Compile Command for Router Nodes

Handles compilation of 'router' type nodes.
"""

from typing import Dict, Any

from app.engine.commands.base import BaseCompileCommand, CompileContext
from app.nodes.router_node import RouterNode
from app.logging import get_logger

logger = get_logger(__name__)


class CompileRouterCommand(BaseCompileCommand):
    """
    Compiles Router nodes into the workflow.
    
    Router nodes provide conditional branching based on LLM output.
    """
    
    node_types = ["router"]
    
    def execute(
        self, 
        node_id: str, 
        node_data: Dict[str, Any], 
        context: CompileContext
    ) -> None:
        """
        Compile a router node.
        
        Args:
            node_id: Unique node identifier
            node_data: Router configuration (routes, conditions)
            context: Shared compilation context
        """
        router_node = RouterNode(node_id, node_data)
        context.workflow.add_node(node_id, router_node)
        context.node_ids.add(node_id)
        
        logger.debug(
            "router_node_compiled", 
            node_id=node_id, 
            routes_count=len(node_data.get('routes', []))
        )
