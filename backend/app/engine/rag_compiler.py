"""
RAG Tools Compiler Integration
Handles collection and distribution of RAG tools to agents during graph compilation.
"""

from typing import Dict, List, Any
from app.logging import get_logger

logger = get_logger(__name__)


def collect_and_bind_rag_tools(nodes: List[Dict], edges: List[Dict], node_map: Dict[str, Dict]):
    """
    Collect RAG tools and bind them to agents based on global_access flag.
    
    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        node_map: Dictionary mapping node IDs to node data
        
    This function modifies node_data['tools'] in-place for agent nodes.
    """
    from app.nodes.rag_node import RAGNode
    
    rag_tools_global = []  # Tools from RAG nodes with global_access=True
    rag_tools_local = {}   # node_id -> tools for RAG nodes with global_access=False
    
    # Step 1: Collect RAG tools
    for node in nodes:
        if node.get('type') == 'rag':
            node_id = node['id']
            node_data = node.get('data', {})
            
            try:
                # Create RAG node instance to get its tools
                rag_node = RAGNode(node_id, node_data)
                tools = rag_node.get_tools()
                
                if rag_node.global_access:
                    # Global: Add to all agents
                    rag_tools_global.extend(tools)
                    logger.debug("rag_tools_global", node_id=node_id, tools=[t.name for t in tools])
                else:
                    # Local: Store for edge-based binding
                    rag_tools_local[node_id] = tools
                    logger.debug("rag_tools_local", node_id=node_id, tools=[t.name for t in tools])
            except Exception as e:
                logger.error("rag_tools_collection_failed", node_id=node_id, error=str(e))
    
    # Step 2: Inject global RAG tools into all agent nodes
    if rag_tools_global:
        logger.debug("injecting_global_rag_tools", count=len(rag_tools_global), tool_names=[t.name for t in rag_tools_global])
        for node in nodes:
            if node.get('type') == 'agent':
                node_id = node['id']
                # CRITICAL: Access node['data'] directly, not node.get('data', {})
                # to ensure we modify the same reference used in compiler.py
                if 'data' not in node:
                    node['data'] = {}
                node_data = node['data']
                
                if 'tools' not in node_data:
                    node_data['tools'] = []
                
                existing_tools = node_data['tools'].copy()
                logger.debug("agent_existing_tools_before_rag", agent_id=node_id, tools=existing_tools)
                
                # Add global RAG tool names
                for tool in rag_tools_global:
                    if tool.name not in node_data['tools']:
                        node_data['tools'].append(tool.name)
                        logger.debug("injecting_global_rag_tool", agent_id=node_id, tool_name=tool.name)
                
                logger.debug("agent_tools_after_rag", agent_id=node_id, tools=node_data['tools'])
    
    # Step 3: Inject local RAG tools based on edges (RAG -> Agent connections)
    for edge in edges:
        source = edge['source']
        target = edge['target']
        
        # If source is a RAG node with local tools
        if source in rag_tools_local:
            target_node = node_map.get(target)
            if target_node and target_node.get('type') == 'agent':
                # CRITICAL: Access target_node['data'] directly
                if 'data' not in target_node:
                    target_node['data'] = {}
                target_data = target_node['data']
                
                if 'tools' not in target_data:
                    target_data['tools'] = []
                
                # Add RAG tools to this specific agent
                for tool in rag_tools_local[source]:
                    if tool.name not in target_data['tools']:
                        target_data['tools'].append(tool.name)
                        logger.debug("injecting_local_rag_tool", agent_id=target, rag_node=source, tool_name=tool.name)
    
    # Step 4: Register all RAG tools in the tool registry
    all_rag_tools = rag_tools_global + [tool for tools in rag_tools_local.values() for tool in tools]
    if all_rag_tools:
        from app.services.tool_registry import register_rag_tools
        register_rag_tools(all_rag_tools)
        logger.debug("rag_tools_registered", count=len(all_rag_tools))
