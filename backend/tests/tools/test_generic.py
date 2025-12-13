import pytest
import os
from app.services.tool_registry import load_tools, get_tool

@pytest.mark.asyncio
async def test_write_tool_lifecycle():
    """Test functionality of the local file writer tool."""
    # Ensure registry loaded
    await load_tools()
    
    tool_name = "write_local_file"
    tool = await get_tool(tool_name)
    assert tool is not None, f"Tool {tool_name} not found"
    
    test_file = "test_pytest_output.txt"
    content = "Hello from Pytest!"
    
    try:
        # Execute
        result = tool.invoke({"file_path": test_file, "content": content})
        assert "Successfully wrote" in result
        
        # Verify file
        assert os.path.exists(test_file)
        with open(test_file, 'r') as f:
            assert f.read() == content
            
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
