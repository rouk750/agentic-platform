"""
Compile Command for Tool Nodes

Handles compilation of 'tool' type nodes.
"""

from typing import Dict, Any

from app.engine.commands.base import BaseCompileCommand, CompileContext
from app.nodes.tool_node import ToolNode
from app.logging import get_logger

logger = get_logger(__name__)


class CompileToolCommand(BaseCompileCommand):
    """
    Compiles Tool nodes into the workflow.
    
    Tool nodes execute tool calls from previous agent messages.
    """
    
    node_types = ["tool"]
    
    def execute(
        self, 
        node_id: str, 
        node_data: Dict[str, Any], 
        context: CompileContext
    ) -> None:
        """
        Compile a tool node.
        
        Args:
            node_id: Unique node identifier
            node_data: Tool configuration (tool_name, label)
            context: Shared compilation context
        """
        tool_node = ToolNode(node_id, node_data)
        context.workflow.add_node(node_id, tool_node)
        context.node_ids.add(node_id)
        
        logger.debug("tool_node_compiled", node_id=node_id)
