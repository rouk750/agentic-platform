from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from typing import Dict, Any, Optional

from app.engine.state import GraphState
from app.nodes.registry import NODE_REGISTRY
from app.engine.router import make_router

def compile_graph(graph_data: Dict[str, Any], checkpointer: Optional[BaseCheckpointSaver] = None):
    """
    Compiles a React Flow JSON graph into a LangGraph StateGraph.
    """
    workflow = StateGraph(GraphState)
    
    
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])
    
    # 1. Add Nodes
    # We first register all nodes.
    # We might need to handle "tools" specifically if they are a separate node type in UI
    # or just a configuration on the agent. 
    # For this Epic, we assume nodes in JSON map to registered classes.
    
    node_ids = set()
    
    for node in nodes:
        node_id = node['id']
        node_type = node['type']
        node_data = node.get('data', {})
        
        node_ids.add(node_id)
        
        if node_type in NODE_REGISTRY:
            node_class = NODE_REGISTRY[node_type]
            
            # Instantiate the node executable
            # Some nodes might be functions, some classes. 
            # Our GenericAgentNode is a class we instantiate.
            try:
                executable = node_class(node_id, node_data)
                workflow.add_node(node_id, executable)
            except Exception as e:
                print(f"Error instantiating node {node_id} ({node_type}): {e}")
                # Potentially raise or skip
                raise e
        else:
             print(f"Warning: Unknown node type {node_type} for node {node_id}")
    
    # 2. Add Edges
    # We need to group edges by source to detect conditional branching.
    # If a source has multiple outgoing edges, it's a conditional node -> router needed.
    # Or strict definition: A node is either linear or conditional.
    # In React Flow, conditional edges might be represented by handles.
    
    adjacency = {} # source -> list of (target, handleId/condition)
    
    for edge in edges:
        source = edge['source']
        target = edge['target']
        source_handle = edge.get('sourceHandle') # e.g. "true", "false", or "default"
        
        if source not in adjacency:
            adjacency[source] = []
        adjacency[source].append({"target": target, "handle": source_handle})

    # Find the start node (Entry point)
    # Strategy:
    # 1. Look for explicit START edge (from a node named 'start_node' or 'START' not in registry)
    # 2. Look for orphans (nodes with no incoming edges from VALID other nodes)
    
    start_edge_found = False
    
    # Calculate incoming edges only from valid nodes to identify orphans correctly
    valid_incoming_edges = set()
    for source, targets in adjacency.items():
        if source in node_ids:
            for t in targets:
                valid_incoming_edges.add(t['target'])
    
    # Check for implicit start edges (source not in node_ids)
    for source, targets in adjacency.items():
        if source not in node_ids:
            # If the source looks like a start node, use its targets as entry points
            if source.lower() in ['start', 'start_node', 'begin']:
                 for t in targets:
                     workflow.add_edge(START, t['target'])
                     start_edge_found = True
            continue 

    if not start_edge_found:
        # Fallback: Find node with no incoming edges from other nodes
        orphans = [nid for nid in node_ids if nid not in valid_incoming_edges]
        if orphans:
            # Connect the first orphan to START
            workflow.add_edge(START, orphans[0])
        else:
            # Fallback 2 (Cycle detection fallback):
            # If no orphans, it means we have a cycle covering all nodes.
            # We arbitrarily (or heuristically) pick an 'agent' node as start.
            agents = [n for n in nodes if n.get('type') == 'agent' or 'agent' in n.get('id', '').lower()]
            if agents:
                workflow.add_edge(START, agents[0]['id'])
            elif nodes:
                 # Fallback 3: Just the first node
                 workflow.add_edge(START, nodes[0]['id'])
            
    # Create a lookup for node data to access configuration
    node_map = {n['id']: n for n in nodes}

    # Process edges for registered nodes
    for source_id, targets in adjacency.items():
        # Only process edges starting from valid nodes
        if source_id not in node_ids: 
            continue
            
        source_node_data = node_map.get(source_id, {})
        source_node_type = source_node_data.get('type')

        # --- 1. Implicit Tool Routing (Agent -> Tool via 'tool-call') ---
        # (Only applies if source is NOT explicitly a router node, though agents act as routers here)
        
        tool_call_target = None
        default_target_for_tool = None
        
        has_tool_handle = False
        for t in targets:
            if t['handle'] == 'tool-call':
                has_tool_handle = True
                tool_call_target = t['target']
            elif not t['handle'] or t['handle'] == 'default' or t['handle'] == 'output':
                default_target_for_tool = t['target']
        
            if has_tool_handle:
                def route_tool(state, config=None, t_target=tool_call_target, d_target=default_target_for_tool):
                    messages = state.get('messages', [])
                    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
                        return t_target
                    return d_target if d_target else END

                path_map = {tool_call_target: tool_call_target}
                if default_target_for_tool:
                    path_map[default_target_for_tool] = default_target_for_tool
                else:
                    path_map[END] = END
                
                workflow.add_conditional_edges(source_id, route_tool, path_map)
                continue

        # --- 2. Explicit Router Node Logic ---
        if source_node_type == 'router':
            # This node is dedicated to routing. 
            # It expects 'routes' in its data: [{ condition: 'contains', value: 'foo', target_handle: 'handle-id' }]
            
            routes_config = source_node_data.get('data', {}).get('routes', [])
            # Map handle_id -> target_node_id
            handle_to_target = {t['handle']: t['target'] for t in targets}
            
            # Default route (handle 'default' or 'else')
            default_route_target = handle_to_target.get('default') or handle_to_target.get('else')
            
            source_label = source_node_data.get("label", f"Router {source_id}")
            router_fn = make_router(routes_config, handle_to_target, default_route_target, source_label=source_label)
            
            # Build path map for validation
            path_map = {}
            for t_node in handle_to_target.values():
                path_map[t_node] = t_node
            if default_route_target:
                path_map[default_route_target] = default_route_target
            else:
                path_map[END] = END
                
            workflow.add_conditional_edges(source_id, router_fn, path_map)
            continue
        
            workflow.add_conditional_edges(source_id, router_fn, path_map)
            continue
        
        # --- 3. Iterator Node Logic (Next vs Complete) ---
        if source_node_type == 'iterator':
            next_target = None
            complete_target = None
            
            for t in targets:
                if t['handle'] == 'next':
                    next_target = t['target']
                elif t['handle'] == 'complete':
                    complete_target = t['target']

            def route_iterator(state, config=None, n_target=next_target, c_target=complete_target):
                # Check _signal in state (set by IteratorNode)
                signal = state.get("_signal", "COMPLETE") 
                if signal == "NEXT":
                    return n_target if n_target else END
                else:
                    return c_target if c_target else END

            path_map = {}
            if next_target: path_map[next_target] = next_target
            if complete_target: path_map[complete_target] = complete_target
            path_map[END] = END
            
            workflow.add_conditional_edges(source_id, route_iterator, path_map)
            continue

        # --- 4. Standard / Fallback Edge Processing ---
        # If we reach here, it means it's not a tool call and not a router node logic.
        # We simply add edges to all targets. LangGraph supports fan-out (state sent to multiple nodes).
        if targets:
            for t in targets:
                target_id = t['target']
                # If target is a special UI end node, map to LangGraph END
                final_target = END if target_id in ["END", "finish_node"] else target_id
                
                # Avoid duplicates if multiple handles point to to duplicate nodes (rare but possible)
                # But LangGraph add_edge is idempotent usually, or we trust the set.
                try:
                    workflow.add_edge(source_id, final_target)
                except Exception as e:
                     print(f"Error adding edge {source_id} -> {final_target}: {e}")
        
    return workflow.compile(checkpointer=checkpointer)
