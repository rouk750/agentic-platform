"""
Compile Command for Iterator Nodes

Handles compilation of 'iterator' type nodes.
"""

from typing import Dict, Any

from app.engine.commands.base import BaseCompileCommand, CompileContext
from app.nodes.iterator_node import IteratorNode
from app.logging import get_logger

logger = get_logger(__name__)


class CompileIteratorCommand(BaseCompileCommand):
    """
    Compiles Iterator nodes into the workflow.
    
    Iterator nodes loop over list items and process each.
    """
    
    node_types = ["iterator"]
    
    def execute(
        self, 
        node_id: str, 
        node_data: Dict[str, Any], 
        context: CompileContext
    ) -> None:
        """
        Compile an iterator node.
        
        Args:
            node_id: Unique node identifier
            node_data: Iterator configuration (input_key, output_key, etc.)
            context: Shared compilation context
        """
        iterator_node = IteratorNode(node_id, node_data)
        context.workflow.add_node(node_id, iterator_node)
        context.node_ids.add(node_id)
        
        logger.debug("iterator_node_compiled", node_id=node_id)
