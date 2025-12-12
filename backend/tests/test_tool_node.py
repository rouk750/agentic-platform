import pytest
from unittest.mock import MagicMock
from app.nodes.tool_node import ToolNode
from app.services.tool_registry import load_tools
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
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
        # Mock config
        config = {"configurable": {"thread_id": "1"}}
        result = await node(state, config)
        print(f"ToolNode Result: {result}")
        
        messages = result.get("messages", [])
        assert messages, "No messages returned"
        assert messages[0].content == "iit s a big fake", f"Unexpected content: {messages[0].content}"
        print("SUCCESS: fake_tool executed correctly via ToolNode.")
            
    except Exception as e:
        pytest.fail(f"EXCEPTION during ToolNode execution: {e}")
