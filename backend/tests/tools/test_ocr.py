import os
import json
from PIL import Image, ImageDraw
from app.tools_library.ocr_tool import extract_text_from_image

def create_test_image(path):
    img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Using default font, but making it larger simply by scaling or just spacing
    d.text((50, 80), "Hello   World", fill=(0, 0, 0)) # Extra spaces
    img.save(path)

def test_ocr():
    test_file = "test_ocr_image.png"
    create_test_image(test_file)
    
    try:
        print(f"Testing OCR on {test_file}...")
        result_json = extract_text_from_image.invoke({"image_path": test_file})
        
        # Check if result looks like an error string or valid JSON
        if result_json.startswith("Error:") or result_json.startswith("Critical error:") or result_json.startswith("Information:"):
             print(f"OCR returned non-JSON message: {result_json}")
             return

        try:
            items = json.loads(result_json)
            print(f"Successfully parsed JSON. Found {len(items)} items.")
            
            # Simple check: join all non-empty text fields
            # Check safely for 'text' key existing
            all_text = " ".join([item['text'] for item in items if 'text' in item and item['text'].strip()!=''])
            print(f"Reconstructed text: '{all_text}'")

            if "Hello" in all_text and "World" in all_text:
                 print("\nSUCCESS: Text 'Hello World' was found in the JSON data.")
            else:
                 print("\nFAILURE: Text 'Hello World' NOT found in JSON data.")
                 print("Dump of items with text:")
                 for item in items:
                     if 'text' in item and item['text'].strip():
                         print(item)

        except json.JSONDecodeError as e:
            print(f"FAILURE: Could not decode JSON. Raw output start: {result_json[:100]}...")
            print(e)
            
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_ocr()
