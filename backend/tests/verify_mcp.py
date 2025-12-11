import sys
import os
import asyncio
import json

# Add backend to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.tool_registry import load_tools, get_tool, list_tools_metadata, cleanup_tools

async def test_mcp_integration():
    print("Initializing MCP Integration Test...")
    try:
        # 1. Load Tools (triggers MCP connection)
        print("Loading tools...")
        await load_tools()
        
        # 2. Check metadata
        print("Checking metadata...")
        tools_meta = await list_tools_metadata()
        print(f"Total tools found: {len(tools_meta)}")
        
        mcp_tool_found = False
        
        for t in tools_meta:
            if "mcp__" in t['name']:
                mcp_tool_found = True
                print(f" - Found MCP Tool: {t['name']}")
                
        if not mcp_tool_found:
            print("❌ No MCP tools found. Check mcp_config.json and server connection.")
            return False
            
        print("✅ MCP tools detected in registry.")
        
        # 3. Try to get specific tool
        mcp_tool_id = next((t['name'] for t in tools_meta if "mcp__" in t['name']), None)
        if not mcp_tool_id:
            return False
            
        print(f"Testing retrieval of tool: {mcp_tool_id}")
        tool = await get_tool(mcp_tool_id)
        
        if not tool:
            print(f"❌ Failed to retrieve tool instance for {mcp_tool_id}")
            return False
            
        print(f"✅ Successfully retrieved tool instance: {tool.name}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("Cleaning up...")
        await cleanup_tools()

if __name__ == "__main__":
    try:
        if asyncio.run(test_mcp_integration()):
            print("✅ MCP Integration Verification Passed")
        else:
            print("❌ MCP Integration Verification Failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Exception: {e}")
        sys.exit(1)
