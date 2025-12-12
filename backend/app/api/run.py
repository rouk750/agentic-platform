from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import logging

from app.engine.compiler import compile_graph
from app.engine.storage import get_graph_checkpointer
from langchain_core.messages import HumanMessage
# We need a way to load graph data. For now, we accept it in the payload or load mock/db.
# The requirement says "load_graph_from_db(graph_id)". 
# We don't have that service yet, so we will expect the graph definition in the init message 
# OR implementing a mock loader.

router = APIRouter()

# Mock loader for now
async def load_graph_from_db(graph_id: str) -> Dict[str, Any]:
    # TODO: Implement actual DB load
    # Return empty structure or raise error if not found
    # For MVP we might need to assume the Frontend sends the JSON first.
    return {"nodes": [], "edges": []} 

@router.websocket("/ws/run/{graph_id}")
async def websocket_endpoint(websocket: WebSocket, graph_id: str):
    await websocket.accept()
    
    try:
        # 1. Initialization: Receive Graph JSON (or load from DB)
        # The prompt implies: "1. Charger et compiler le graphe ... graph_data = load_graph_from_db(graph_id)"
        # But since we are building the tool and the user draws it, 
        # normally we save the graph first via REST API, then Run it via WS.
        # Assuming the graph is saved. We'll use a placeholder or check if US 2 was implemented (it says "Epic 2 (Le JSON du graphe est disponible)").
        # So we assume there IS a way to get it. 
        # I'll add a provisional "graph_data" load.
        
        # For now, if load_graph_from_db returns empty, we might try to receive it from WS for dev testing.
        # Check first message.
        init_data = await websocket.receive_json()
        
        graph_data = None
        if "graph" in init_data:
             graph_data = init_data["graph"]
        else:
             # Assume load from DB
             # graph_data = await load_graph_from_db(graph_id)
             pass
        
        if not graph_data:
            await websocket.send_json({"error": "No graph data provided"})
            await websocket.close()
            return

        # Setup Persistence - use context manager
        # checkpointer is an AsyncContextManager, so we must use 'async with'
        cm = await get_graph_checkpointer()
        async with cm as checkpointer:
            # Compile
            app = compile_graph(graph_data, checkpointer=checkpointer)
            
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
            
            async for event in app.astream_events(inputs, config=config, version="v2"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        await websocket.send_json({"type": "token", "content": content})
                        
                elif kind == "on_chain_start":
                    # Detect if it's a node start
                    node_name = event["name"]
                    if node_name and node_name not in ["__start__", "__end__", "LangGraph", "route_tool", "route_iterator"]:
                        await websocket.send_json({"type": "node_active", "node_id": node_name})
                
                elif kind == "on_chain_end":
                     # Pass the output which might contain metadata like _iterator_metadata
                     output = event["data"].get("output")
                     
                     # Safe serialization for frontend:
                     # Only pull out specific metadata we need to avoid "Object not serializable" errors
                     # with complex LangChain objects.
                     safe_data = {}
                     if isinstance(output, dict) and "_iterator_metadata" in output:
                         safe_data["_iterator_metadata"] = output["_iterator_metadata"]
                         
                     await websocket.send_json({
                         "type": "node_finished", 
                         "node_id": event["name"],
                         "data": safe_data
                     })

                elif kind == "on_tool_start":
                    await websocket.send_json({
                        "type": "tool_start", 
                        "name": event["name"], 
                        "input": event["data"].get("input")
                    })

                elif kind == "on_tool_end":
                    await websocket.send_json({
                        "type": "tool_end", 
                        "name": event["name"], 
                        "output": event["data"].get("output")
                    })
                     
            await websocket.send_json({"type": "done"})
        
    except WebSocketDisconnect:
        print(f"Client disconnected {graph_id}")
    except Exception as e:
        print(f"Error in execution: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
