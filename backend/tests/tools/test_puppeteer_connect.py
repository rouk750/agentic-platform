import asyncio
import os
import sys
import json

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.services.tool_registry import load_tools, get_tool, cleanup_tools

async def main():
    try:
        print("Loading tools...")
        await load_tools()
        
        target_tool = "mcp__puppeteer__puppeteer_connect_active_tab"
        print(f"Getting tool {target_tool}...")
        tool = await get_tool(target_tool)
        
        if tool:
            print(f"Tool found: {tool.name}")
            print("Tool Schema:")
            print(json.dumps(tool.args, indent=2))
            
            # Execute it
            print(f"Executing {target_tool}...")
            # It likely takes no args or maybe a browser_url? Let's check schema first output above.
            # But we'll try with empty args first if schema is empty.
            args = {} 
            
            try:
                result = await tool.ainvoke(args)
                print("Execution Result:")
                print(result)
            except Exception as e:
                print(f"Execution Failed: {e}")
                
        else:
            print(f"Tool {target_tool} not found.")

    finally:
        await cleanup_tools()

if __name__ == "__main__":
    asyncio.run(main())
