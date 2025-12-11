import sys
import os

# Add backend to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.tool_registry import load_tools, get_tool
from langchain_core.messages import ToolMessage

def test_write_tool():
    print("Loading tools...")
    load_tools()
    
    tool_name = "write_local_file"
    tool = get_tool(tool_name)
    
    if not tool:
        print(f"❌ Tool '{tool_name}' not found in registry.")
        return False
        
    print(f"✅ Tool '{tool_name}' found.")
    
    # Test writing
    test_file = "test_write_tool_output.txt"
    content = "Hello, Agentic World!"
    
    print(f"Testing write to {test_file}...")
    try:
        # LangChain tools are callable directly or via .invoke
        result = tool.invoke({"file_path": test_file, "content": content})
        print(f"Tool output: {result}")
        
        if "Successfully wrote" in result and os.path.exists(test_file):
             with open(test_file, 'r') as f:
                 read_content = f.read()
                 if read_content == content:
                     print("✅ File content verified.")
                 else:
                     print(f"❌ Content mismatch. Expected '{content}', got '{read_content}'")
                     return False
        else:
            print("❌ File write failed or file not found.")
            return False
            
        # Clean up
        os.remove(test_file)
        print("Test file cleaned up.")
        return True
        
    except Exception as e:
        print(f"❌ Exception during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_write_tool():
        print("✅ Write Tool Verification Passed")
    else:
        print("❌ Write Tool Verification Failed")
        sys.exit(1)
