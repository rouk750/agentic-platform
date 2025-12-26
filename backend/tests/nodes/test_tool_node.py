import pytest
import os
from unittest.mock import MagicMock
from app.nodes.tool_node import ToolNode
from app.services.tool_registry import load_tools
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_tool_node():
    print("Loading tools...")
    await load_tools()
    
    # Setup - Create temp file
    filename = "test_tool_node_temp.txt"
    content_str = "Secret Content for ToolNode"
    with open(filename, "w") as f:
        f.write(content_str)
        
    try:
        # Setup ToolNode
        node = ToolNode(node_id="test_tool_node")
        
        # Mock State with a tool call
        tool_call = {
            'name': 'read_local_file',
            'args': {'file_path': filename},
            'id': 'call_123'
        }
        
        last_message = AIMessage(content="", tool_calls=[tool_call])
        state = {"messages": [last_message]}
        
        print("Invoking ToolNode...")
        config = {"configurable": {"thread_id": "1"}}
        result = await node(state, config)
        print(f"ToolNode Result: {result}")
        
        messages = result.get("messages", [])
        assert messages, "No messages returned"
        assert content_str in messages[0].content, f"Unexpected content: {messages[0].content}"
        print("SUCCESS: read_local_file executed correctly via ToolNode.")
            
    except Exception as e:
        pytest.fail(f"EXCEPTION during ToolNode execution: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
