import pytest
from app.services.tool_registry import load_tools, list_tools_metadata, get_tool, cleanup_tools

@pytest.mark.asyncio
async def test_mcp_registry_logic():
    """Verify tool registry can load and list tools, detecting MCP if present."""
    try:
        await load_tools()
        tools = await list_tools_metadata()
        assert len(tools) > 0
        
        # Check if we have at least standard tools
        names = [t["name"] for t in tools]
        assert "write_local_file" in names
        assert "read_local_file" in names
        
        # Optional: Check for MCP tools if config exists
        # We don't assert hard failure if MCP is missing since this runs in CI potentially without MCP server
        mcp_tools = [t for t in tools if "mcp__" in t["name"]]
        if mcp_tools:
            print(f"Detected {len(mcp_tools)} MCP tools.")
            # Try getting one
            t_instance = await get_tool(mcp_tools[0]["name"])
            assert t_instance is not None
            
    finally:
        await cleanup_tools()
