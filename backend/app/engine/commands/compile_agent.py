"""
Compile Command for Agent Nodes

Handles compilation of 'agent' type nodes.
"""

from typing import Dict, Any

from app.engine.commands.base import BaseCompileCommand, CompileContext
from app.nodes.agent import GenericAgentNode
from app.logging import get_logger

logger = get_logger(__name__)


class CompileAgentCommand(BaseCompileCommand):
    """
    Compiles Agent nodes into the workflow.
    
    Handles:
    - Creating GenericAgentNode instances
    - Injecting tools discovered from edges
    - Setting up interrupt points for HITL
    """
    
    node_types = ["agent"]
    
    def execute(
        self, 
        node_id: str, 
        node_data: Dict[str, Any], 
        context: CompileContext
    ) -> None:
        """
        Compile an agent node.
        
        Args:
            node_id: Unique node identifier
            node_data: Agent configuration (profile_id, system_prompt, tools, etc.)
            context: Shared compilation context
        """
        # Inject tools discovered from edges
        if node_id in context.extra_tools_map:
            if 'tools' not in node_data:
                node_data['tools'] = []
            
            for tool_name in context.extra_tools_map[node_id]:
                if tool_name not in node_data['tools']:
                    logger.debug("injecting_edge_tool", node_id=node_id, tool=tool_name)
                    node_data['tools'].append(tool_name)
        
        # Create agent node
        agent_node = GenericAgentNode(node_id, node_data)
        context.workflow.add_node(node_id, agent_node)
        
        # Track node
        context.node_ids.add(node_id)
        
        # Check for HITL interrupt
        if node_data.get('require_approval', False):
            context.interrupt_nodes.append(node_id)
        
        logger.debug("agent_node_compiled", node_id=node_id, tools=node_data.get('tools', []))
