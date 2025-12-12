
import asyncio
import os
import sys
from unittest.mock import MagicMock

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.nodes.tool_node import ToolNode
from app.services.tool_registry import load_tools
from langchain_core.messages import AIMessage

async def test_tool_node():
    print("Loading tools...")
    await load_tools()
    
    # Setup ToolNode
    node = ToolNode(node_id="test_tool_node")
    
    # Mock State with a tool call
    # Tool call format: {'name': 'fake_tool', 'args': {}, 'id': 'call_123'}
    tool_call = {
        'name': 'fake_tool',
        'args': {},
        'id': 'call_123'
    }
    
    last_message = AIMessage(content="", tool_calls=[tool_call])
    state = {"messages": [last_message]}
    
    print("Invoking ToolNode...")
    try:
        result = await node(state)
        print(f"ToolNode Result: {result}")
        
        messages = result.get("messages", [])
        if messages and messages[0].content == "iit s a big fake":
            print("SUCCESS: fake_tool executed correctly via ToolNode.")
        else:
            print("FAILURE: Unexpected output.")
            
    except Exception as e:
        print(f"EXCEPTION during ToolNode execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_node())
