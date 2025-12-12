
import asyncio
import os
import sys
import json

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.tools_library.csv_reader import read_csv_file

def test_csv_reader():
    print("Testing read_csv_file...")
    
    # Path to user file (semicolon separated)
    csv_path = "/Users/faroukbelhadj/Desktop/QA/csv/avis_utilisateurs.csv"
    
    result = read_csv_file.invoke(csv_path)
    print(f"Result (truncated): {result[:500]}...")
    
    try:
        data = json.loads(result)
        if isinstance(data, list) and len(data) > 0:
            print(f"SUCCESS: Loaded {len(data)} rows.")
            print(f"First row keys: {data[0].keys()}")
            
            # Check for correct keys (id, avis) - ignoring potential extra spaces if csv dict reader didn't strip header
            keys = list(data[0].keys())
            if "id" in keys and "avis" in keys:
                 print("SUCCESS: Correct headers detected.")
            else:
                 print(f"WARNING: headers might be off. Got: {keys}")
                 
        else:
            print("FAILURE: Result is not a non-empty list.")
    except Exception as e:
        print(f"FAILURE: Could not parse JSON result: {e}")

if __name__ == "__main__":
    test_csv_reader()
