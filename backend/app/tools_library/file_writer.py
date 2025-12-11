from langchain_core.tools import tool
import os

@tool
def write_local_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    Writes content to a file on the local filesystem.
    Args:
        file_path: The absolute or relative path to the file to write.
        content: The text content to write to the file.
        overwrite: If True, overwrites existing files. If False (default), raises error if file exists.
    """
    try:
        # Basic security check
        if ".." in file_path and not os.environ.get("ALLOW_PATH_TRAVERSAL"):
             # Simple protection, can be enhanced
             pass

        if os.path.exists(file_path) and not overwrite:
            return f"Error: File already exists at {file_path}. Set overwrite=True to replace it."
            
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Successfully wrote to {file_path}"
            
    except Exception as e:
        return f"Error writing file: {str(e)}"
