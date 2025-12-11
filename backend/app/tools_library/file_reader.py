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
        # Sanitize input: strip whitespace and quotes that LLMs might hallucinate
        clean_path = file_path.strip().strip("'").strip('"')
        
        # Expand user path (e.g. ~/Desktop...)
        clean_path = os.path.expanduser(clean_path)
        
        if not os.path.exists(clean_path):
            # Try to resolve relative to current working directory explicitly for better error message
            abs_path = os.path.abspath(clean_path)
            return f"Error: File not found at {clean_path} (resolved to {abs_path})"
            
        # Try reading with utf-8 first, fallback to latin-1
        try:
            with open(clean_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(clean_path, 'r', encoding='latin-1') as f:
                return f.read()
            
    except Exception as e:
        return f"Error reading file: {str(e)}"
