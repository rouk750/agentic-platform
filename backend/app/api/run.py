from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import logging
import os
import asyncio

from app.engine.compiler import compile_graph
from app.engine.storage import get_graph_checkpointer
from langchain_core.messages import HumanMessage
# We need a way to load graph data. For now, we accept it in the payload or load mock/db.
# The requirement says "load_graph_from_db(graph_id)". 
# We don't have that service yet, so we will expect the graph definition in the init message 
# OR implementing a mock loader.

router = APIRouter()

# Mock loader for now

from app.database import engine
from sqlmodel import Session, select
from app.models.flow import Flow

def sync_subgraph_loader(flow_id_str: str) -> Dict[str, Any]:
    """
    Synchronously load a flow definition from the DB.
    Used by the compiler for recursive subgraph loading.
    """
    try:
        fid = int(flow_id_str)
    except ValueError:
        raise ValueError(f"Invalid Flow ID format: {flow_id_str}")
        
    with Session(engine) as session:
        flow = session.get(Flow, fid)
        if not flow:
            raise ValueError(f"Subgraph Flow {fid} not found in database.")
        if not flow.data:
             return {"nodes": [], "edges": []}
        return json.loads(flow.data)

@router.websocket("/ws/run/{graph_id}")
async def websocket_endpoint(websocket: WebSocket, graph_id: str):
    await websocket.accept()
    
    try:
        # 1. Initialization
        init_data = await websocket.receive_json()
        
        graph_data = None
        if "graph" in init_data:
             graph_data = init_data["graph"]
        else:
             # Load from DB if not in payload
             # usage: sync_subgraph_loader serves as a generic loader too
             try:
                 graph_data = await asyncio.to_thread(sync_subgraph_loader, graph_id)
             except Exception as e:
                 print(f"Failed to load graph {graph_id}: {e}")
        
        if not graph_data:
            await websocket.send_json({"error": "No graph data provided or found."})
            await websocket.close()
            return

        # Setup Persistence
        cm = await get_graph_checkpointer()
        async with cm as checkpointer:
            # Compile with Subgraph Support
            app = await asyncio.to_thread(
                compile_graph,
                graph_data, 
                checkpointer=checkpointer,
                subgraph_loader=sync_subgraph_loader
            )
            
            # 2. Input Handling
            user_input = init_data.get("input")
            thread_id = init_data.get("thread_id", "default_thread")
            
            if not user_input:
                # Wait for input
                msg = await websocket.receive_json()
                user_input = msg.get("input")
                
            inputs = {"messages": [HumanMessage(content=user_input)]}
            config = {"configurable": {"thread_id": thread_id}}
            
            # 3. Execution with Streaming
            recursion_limit = init_data.get("recursion_limit", 50)
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": recursion_limit
            }
            
            # Use current_inputs for the loop
            current_inputs = inputs

            while True:
                # Update recursion limit dynamically
                config["recursion_limit"] = int(os.getenv("LANGGRAPH_RECURSION_LIMIT", "50"))
                
                async for event in app.astream_events(current_inputs, config=config, version="v2"):
                    kind = event["event"]
                    
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            # Attempt to find node_id
                            from app.utils.observability_utils import extract_node_id
                            node_id = extract_node_id(event)

                            await websocket.send_json({
                                "type": "token", 
                                "content": content,
                                "node_id": node_id
                            })
                            
                    elif kind == "on_chat_model_end":
                         # [FEATURE] Token Tracking
                         output = event["data"].get("output")
                         if output and hasattr(output, "usage_metadata") and output.usage_metadata:
                             usage = output.usage_metadata
                             
                             # Find node_id
                             from app.utils.observability_utils import extract_node_id
                             node_id = extract_node_id(event)
                                 
                             if node_id:
                                 await websocket.send_json({
                                     "type": "token_usage",
                                     "node_id": node_id,
                                     "usage": usage
                                 })         
                    elif kind == "on_chain_start":
                        # Detect if it's a node start
                        node_name = event["name"]
                        if node_name and node_name not in ["__start__", "__end__", "LangGraph", "route_tool", "route_iterator"]:
                            node_input = event["data"].get("input") or event["data"]

                            from app.utils.observability_utils import make_serializable
                            safe_input = make_serializable(node_input)
                            
                            if isinstance(safe_input, dict):
                                 try:
                                     json.dumps(safe_input)
                                 except TypeError:
                                     safe_input = str(node_input)

                            await websocket.send_json({
                                "type": "node_active", 
                                "node_id": node_name,
                                "input": safe_input
                            })
                    
                    elif kind == "on_chain_end":
                         output = event["data"].get("output")
                         safe_data = {}
                         if isinstance(output, dict) and "_iterator_metadata" in output:
                             safe_data["_iterator_metadata"] = output["_iterator_metadata"]
                         
                         # [FEATURE] Tool Highlighting Persistence
                         # Check if output contains tool calls (Agent -> Tool)
                         has_tool_calls = False
                         if hasattr(output, "tool_calls") and output.tool_calls:
                             has_tool_calls = True
                         elif isinstance(output, dict) and output.get("tool_calls"):
                             has_tool_calls = True
                         # [FIX] Handle standard LangGraph dict return {"messages": [AIMessage]}
                         elif isinstance(output, dict) and "messages" in output:
                             msgs = output["messages"]
                             if msgs and hasattr(msgs[-1], "tool_calls") and msgs[-1].tool_calls:
                                 has_tool_calls = True
                         
                         safe_data["has_tool_calls"] = has_tool_calls
 
                         # [FEATURE] Deep Observability Snapshot
                         # Fetch the full state after this node's execution
                         timestamp = None # Add timestamp if possible
                         snapshot_payload = None
                         
                         # Identify if this is a significant node (not LangGraph internals)
                         if event["name"] and event["name"] not in ["__start__", "__end__", "LangGraph", "route_tool", "route_iterator"]:
                             try:
                                 # Fetch the latest state from the checkpointer
                                 state_snapshot = await app.aget_state(config)
                                 if state_snapshot:
                                     # Serialize the state
                                     # Messages need specific handling to be JSON serializable
                                     from langchain_core.messages import messages_to_dict
                                     
                                     current_values = state_snapshot.values
                                     serialized_state = {}
                                     
                                     if "messages" in current_values:
                                         serialized_state["messages"] = messages_to_dict(current_values["messages"])
                                     
                                     if "context" in current_values:
                                         serialized_state["context"] = current_values["context"]

                                     snapshot_payload = {
                                         "node_id": event["name"],
                                         "state": serialized_state,
                                         "created_at": state_snapshot.created_at if hasattr(state_snapshot, "created_at") else None,
                                         "config": state_snapshot.config
                                     }
                             except Exception as exc:
                                 print(f"Error fetching snapshot for {event['name']}: {exc}")

                         await websocket.send_json({
                             "type": "node_finished", 
                             "node_id": event["name"],
                             "data": safe_data,
                             "snapshot": snapshot_payload # Piggyback on node_finished
                         })

                    elif kind == "on_tool_start":
                        from app.utils.observability_utils import extract_node_id
                        node_id = extract_node_id(event)

                        await websocket.send_json({
                            "type": "tool_start", 
                            "name": event["name"], 
                            "input": event["data"].get("input"),
                            "node_id": node_id
                        })

                    elif kind == "on_tool_end":
                        from app.utils.observability_utils import extract_node_id
                        node_id = extract_node_id(event)

                        await websocket.send_json({
                            "type": "tool_end", 
                            "name": event["name"], 
                            "output": event["data"].get("output"),
                            "node_id": node_id
                        })
                
                # Check for interruption (HITL)
                snapshot = await app.aget_state(config)
                if snapshot.next:
                    # Paused at a breakpoint
                    next_node = snapshot.next[0]
                    await websocket.send_json({"type": "interrupt", "node_id": next_node})
                    
                    # Wait for Resume command
                    cmd = await websocket.receive_json()
                    if cmd.get("command") == "resume":
                         # Resume with None input to proceed from breakpoint
                         current_inputs = None 
                         continue
                    else:
                        # Cancel or other command (e.g. update state?)
                        break
                else:
                    # Completed
                    await websocket.send_json({"type": "done"})
                    break
        
    except WebSocketDisconnect:
        print(f"Client disconnected {graph_id}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in execution: {e}")
        error_message = str(e)
        if not error_message:
            error_message = f"Unknown error ({type(e).__name__})"
            
        if "prompt too long" in str(e) or "context length" in str(e).lower():
            friendly_message = (
                "⚠️ **Context Limit Exceeded**\n\n"
                "The conversation history is too long for the selected model (Context Window Full).\n\n"
                "**Solutions:**\n"
                "1. **Clear Session**: Use the eraser icon to start fresh.\n"
                "2. **Reset**: Use a different model with a larger context window.\n"
                "3. **Optimize**: The system has already truncated tool outputs, but the history is still too large."
            )
            await websocket.send_json({"type": "error", "message": friendly_message})
        else:
            await websocket.send_json({"type": "error", "message": error_message})
        await websocket.close()
