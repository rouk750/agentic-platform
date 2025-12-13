
import sys
import os
import json

# Add current directory to path so we can import app if needed
sys.path.append(os.getcwd())

try:
    from app.tools_library.ocr_tool import extract_text_from_image
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    from app.tools_library.ocr_tool import extract_text_from_image

image_path = "/Users/faroukbelhadj/Desktop/agentic-platform/screenshots/ocr_analysis_1.png"
search_text = "Refuser et fermer"

print(f"Testing OCR on: {image_path}")
print(f"Searching for: '{search_text}'")

try:
    result = extract_text_from_image.invoke({
        "image_path": image_path, 
        "light": True,
        "group_by": "line",
        "search_text": search_text
    })
    
    if "Information: No data" in result:
        print(f"FAILURE: Search returned no results.")
        print(f"Raw Output: {result}")
    else:
        data = json.loads(result)
        print(f"Found {len(data)} matches.")
        for item in data:
            print(f"Match: '{item['text']}' | Similarity: {item.get('similarity')}")
            
except Exception as e:
    print(f"An error occurred: {e}")
