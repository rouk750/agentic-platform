
import pytest
import os
import json
import csv
from app.tools_library.csv_reader import read_csv_file

@pytest.mark.asyncio
async def test_csv_reader_tool(tmp_path):
    """Test functionality of the CSV reader tool using a temporary file."""
    
    # Create a dummy CSV file
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "test.csv"
    
    csv_content = [
        ["id", "avis"],
        ["1", "Great product!"],
        ["2", "Not so good."]
    ]
    
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(csv_content)
        
    csv_path = str(p)
    
    # helper to run synchronously if tool is synchronous, or await if async
    # The original script used .invoke() which is direct.
    result = read_csv_file.invoke(csv_path)
    
    # Validate result is a JSON string
    assert isinstance(result, str)
    
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        pytest.fail(f"Tool output is not valid JSON: {result}")
        
    assert isinstance(data, list)
    assert len(data) == 2
    
    # Check headers/keys
    first_row = data[0]
    # Keys might have whitespace issues if the tool doesn't handle them, 
    # but our simple writer shouldn't introduce them unless we added spaces.
    assert "id" in first_row
    assert "avis" in first_row
    
    assert first_row["id"] == "1"
    assert first_row["avis"] == "Great product!"
    assert data[1]["id"] == "2"
    assert data[1]["avis"] == "Not so good."
