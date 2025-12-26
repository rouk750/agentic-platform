"""
Compile Command for Smart Nodes

Handles compilation of 'smart_node' type nodes (DSPy).
"""

from typing import Dict, Any

from app.engine.commands.base import BaseCompileCommand, CompileContext
from app.nodes.smart_node import SmartNode
from app.logging import get_logger

logger = get_logger(__name__)


class CompileSmartNodeCommand(BaseCompileCommand):
    """
    Compiles Smart nodes (DSPy) into the workflow.
    
    Smart nodes use DSPy for structured input/output processing.
    """
    
    node_types = ["smart_node"]
    
    def execute(
        self, 
        node_id: str, 
        node_data: Dict[str, Any], 
        context: CompileContext
    ) -> None:
        """
        Compile a smart node.
        
        Args:
            node_id: Unique node identifier
            node_data: SmartNode configuration (inputs, outputs, goal, etc.)
            context: Shared compilation context
        """
        smart_node = SmartNode(node_id, node_data)
        context.workflow.add_node(node_id, smart_node)
        context.node_ids.add(node_id)
        
        logger.debug("smart_node_compiled", node_id=node_id, goal=node_data.get('goal', '')[:50])
