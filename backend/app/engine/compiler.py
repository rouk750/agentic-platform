from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from typing import Dict, Any, Optional, Callable

from app.engine.state import GraphState
from app.nodes.registry import NODE_REGISTRY
from app.engine.router import make_router
from app.nodes.agent import GenericAgentNode
from app.nodes.tool_node import ToolNode
from app.nodes.iterator_node import IteratorNode

def compile_graph(graph_data: Dict[str, Any], checkpointer: Optional[BaseCheckpointSaver] = None, subgraph_loader: Optional[Callable[[str], Dict[str, Any]]] = None, recursion_depth: int = 0, visited_flow_ids: set = None) -> Any:
    """
    Compiles a React Flow JSON graph into a LangGraph StateGraph.
    
    Args:
        graph_data: The JSON definition of the graph (nodes, edges).
        checkpointer: Optional persistence mock or object (e.g. SqliteSaver).
        subgraph_loader: Async/Sync function to load a graph Definition by ID. Required for 'subgraph' nodes.
        recursion_depth: Safety limit for nesting.
        visited_flow_ids: Set of Flow IDs continuously visited in this branch to detect cycles.
    """
    if recursion_depth > 5:
        raise ValueError("Max recursion depth reached for subgraphs (5). Check for cyclic dependencies.")

    if visited_flow_ids is None:
        visited_flow_ids = set()

    workflow = StateGraph(GraphState)
    
    
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])
    
    # 1. Add Nodes
    # We first register all nodes.
    # We might need to handle "tools" specifically if they are a separate node type in UI
    # or just a configuration on the agent. 
    # For this Epic, we assume nodes in JSON map to registered classes.
    
    node_ids = set()
    interrupt_nodes = []
    # print(f"DEBUG: Processing nodes with visited: {visited_flow_ids}")
    
    for node in nodes:
        node_id = node['id']
        node_type = node['type']
        node_data = node.get('data', {})
        
        node_ids.add(node_id)
        if node_data.get('require_approval', False):
             interrupt_nodes.append(node_id)
             
        # print(f"DEBUG: Processing node {node_id} type {node_type}")
        
        if node_type == "agent":
            agent_node = GenericAgentNode(node_id, node_data)
            workflow.add_node(node_id, agent_node)
        elif node_type == "tool":
            tool_name = node_data.get("tool_name") or node_data.get("label")
            tool_node = ToolNode(node_id, node_data)
            workflow.add_node(node_id, tool_node)
        elif node_type == "iterator":
            iterator_node = IteratorNode(node_id, node_data)
            workflow.add_node(node_id, iterator_node)
        elif node_type == "subgraph":
            # [FEATURE] Subgraph Support
            if not subgraph_loader:
                raise ValueError(f"Subgraph node '{node_id}' found but no 'subgraph_loader' provided.")
            
            subflow_id = node_data.get("flow_id")
            if not subflow_id:
                raise ValueError(f"Subgraph node '{node_id}' is missing 'flow_id' in data.")
            
            if str(subflow_id) in visited_flow_ids:
                raise ValueError(f"Cyclic dependency detected: Flow contains a Subgraph pointing to an ancestor Flow ID {subflow_id}.")

            # Load Subgraph Definition
            # Note: subgraph_loader might be async, but compile_graph is currently sync.
            # We assume for now subgraph_loader provided is synchronous/blocking or pre-loaded.
            # If `run.py` calls this, it might need to pre-fetch.
            # However, `load_graph_from_db` in run.py is async.
            # CRITICAL: LangGraph construction is sync. We need the definition NOW.
            
            try:
                # Assuming the loader given handles the sync/async bridge or is just sync
                subgraph_def = subgraph_loader(subflow_id) 
                
                # Recursive Compilation
                new_visited = visited_flow_ids.copy()
                new_visited.add(str(subflow_id))
                
                compiled_subgraph = compile_graph(
                    subgraph_def, 
                    checkpointer=None, # Subgraphs usually share state or don't manage their own checkpointing in the same way? 
                                       # Actually they can having their own checkpointer but usually we want one global.
                                       # Passing None to let parent manage it (or pass same checkpointer?)
                    subgraph_loader=subgraph_loader,
                    recursion_depth=recursion_depth + 1,
                    visited_flow_ids=new_visited
                )
                
                workflow.add_node(node_id, compiled_subgraph)
                
            except Exception as e:
                raise ValueError(f"Failed to compile subgraph '{node_id}' (Flow {subflow_id}): {str(e)}")
        elif node_type in NODE_REGISTRY: # Fallback for other registered nodes
            node_class = NODE_REGISTRY[node_type]
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
    # 0. Look for explicit "isStart" flag in node data (User configured)
    # 1. Look for explicit START edge (from a node named 'start_node' or 'START' not in registry)
    # 2. Look for orphans (nodes with no incoming edges from VALID other nodes)
    
    start_edge_found = False
    
    # Create a lookup for node data to access configuration
    node_map = {n['id']: n for n in nodes}

    # 0. Explicit Configuration Check
    for node in nodes:
        if node.get('data', {}).get('isStart', False):
             print(f"DEBUG_COMPILER: Found explicit start node: {node['id']}")
             workflow.add_edge(START, node['id'])
             start_edge_found = True
             # We assume only one start node for now, or multiple are allowed fan-out
    
    # Check for implicit start edges (source not in node_ids) if not found yet
    if not start_edge_found:
        for source, targets in adjacency.items():
            if source not in node_ids:
                # If the source looks like a start node, use its targets as entry points
                if source.lower() in ['start', 'start_node', 'begin']:
                     for t in targets:
                         workflow.add_edge(START, t['target'])
                         start_edge_found = True
                continue 

    if not start_edge_found:
        # Calculate incoming edges only from valid nodes to identify orphans correctly
        valid_incoming_edges = set()
        for source, targets in adjacency.items():
            if source in node_ids:
                # OPTIMIZATION: Ignore edges coming from 'iterator' nodes for orphan detection.
                source_node = node_map.get(source)
                if source_node and source_node.get('type') == 'iterator':
                    continue
                    
                for t in targets:
                    valid_incoming_edges.add(t['target'])

        # Fallback: Find node with no incoming edges from other nodes (ignoring iterators)
        orphans = [n['id'] for n in nodes if n['id'] not in valid_incoming_edges]
        
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
        default_targets_for_tool = []
        
        has_tool_handle = False
        for t in targets:
            if t['handle'] == 'tool-call':
                has_tool_handle = True
                tool_call_target = t['target']
            elif not t['handle'] or t['handle'] == 'default' or t['handle'] == 'output':
                # [FIX] Support fan-out: Collect ALL default targets
                default_targets_for_tool.append(t['target'])
        
        if has_tool_handle:
            def route_tool(state, config=None, t_target=tool_call_target, d_targets=default_targets_for_tool):
                messages = state.get('messages', [])
                if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
                    return t_target
                # [FIX] Return LIST of targets for parallel execution
                return d_targets if d_targets else END

            path_map = {tool_call_target: tool_call_target}
            if default_targets_for_tool:
                for dt in default_targets_for_tool:
                    path_map[dt] = dt
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
                if final_target != END and final_target not in node_ids:
                     print(f"Warning: Edge target {final_target} not found in node registry. Skipping.")
                     continue
                     
                try:
                    workflow.add_edge(source_id, final_target)
                except Exception as e:
                     print(f"Error adding edge {source_id} -> {final_target}: {e}")
        
    return workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt_nodes)
