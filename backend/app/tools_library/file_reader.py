from langchain_core.tools import tool
import os

@tool
def read_local_file(file_path: str) -> str:
    """
    Reads the content of a file from the local filesystem.
    Args:
        file_path: The absolute or relative path to the file to read.
    """
    try:
        # Security check: prevent reading outside of project or specific bounds if needed.
        # For this local desktop app, we might allow full access, but let's be slightly careful.
        # user wants "reelement fonctionnel".
        
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        return f"Error reading file: {str(e)}"
