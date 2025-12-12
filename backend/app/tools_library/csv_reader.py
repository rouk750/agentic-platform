import csv
import json
import os
from langchain_core.tools import tool

@tool
def read_csv_file(file_path: str) -> str:
    """
    Reads a local CSV file, detects the delimiter automatically (e.g. comma or semicolon),
    and returns the content as a JSON string representing a list of objects.
    
    Args:
        file_path (str): The absolute path to the CSV file.
        
    Returns:
        str: A JSON string where each row is an object with keys from the header.
             Returns an error message starting with "Error:" if something goes wrong.
    """
    try:
        # Sanitize path
        file_path = file_path.strip().strip("'").strip('"')
        
        # Expand user path
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
            
        # Try reading with utf-8, fallback to latin-1
        content = None
        encoding = 'utf-8'
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            encoding = 'latin-1'
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
                
        if not content:
            return "Error: File is empty."
            
        # Detect dialect (delimiter)
        try:
            # Analyze the first few lines (e.g. 1024 bytes) to guess the dialect
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(content[:2048])
        except csv.Error:
            # Fallback to default excel (comma) if sniffing fails
            dialect = 'excel'
            
        # Reset file pointer or just use content we read
        from io import StringIO
        f = StringIO(content)
        
        reader = csv.DictReader(f, dialect=dialect)
        rows = list(reader)
        
        return json.dumps(rows, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Error reading CSV: {str(e)}"
