
import pytest
import os
from app.tools_library.file_reader import read_local_file


@pytest.mark.asyncio
async def test_read_local_file():
    """Test reading a file from disk."""
    filename = "test_read.txt"
    content = "Secret Content"
    
    with open(filename, "w") as f:
        f.write(content)
        
    try:
        # Tool function is sync or async? Implementation is usually sync wrapped or async.
        # Let's check import. It's usually a StructuredTool or function.
        # In current codebase, we likely import the callable or the tool object.
        # Assuming it's the function or we wrapt it.
        # If it's a StructuredTool, we call .invoke or .run
        
        # Checking implementation of file_reader.py in previous steps not done, 
        # but usually standard LangChain tools.
        # Let's try calling it directly if it's a function, or .invoke if tool.
        
        # If imports fail, this test will fail fast.
        
        # 1. Direct function call if available (often tools are decorated functions)
        # If `read_local_file` is the tool Object:
        if hasattr(read_local_file, "invoke"):
            result = read_local_file.invoke({"file_path": filename})
        else:
            # It might be the raw function
            result = read_local_file(filename)
            
        assert content in result
        
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def test_read_nonexistent_file():
    """Test error handling for missing file."""
    if hasattr(read_local_file, "invoke"):
        result = read_local_file.invoke({"file_path": "phantom.txt"})
    else:
        result = read_local_file("phantom.txt")
        
    assert "Error" in result or "No such file" in result


