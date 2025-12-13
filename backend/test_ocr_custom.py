
import sys
import os

# Add current directory to path so we can import app if needed
# Assuming we run this from 'backend' directory
sys.path.append(os.getcwd())

try:
    from app.tools_library.ocr_tool import extract_text_from_image
except ImportError:
    # Fallback if running from a different context or structure is different
    print("Could not import directly, trying to add backend to path explicitly")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    from app.tools_library.ocr_tool import extract_text_from_image

image_path = "/Users/faroukbelhadj/Desktop/agentic-platform/screenshots/hotel_bb_home.png"

print(f"Testing OCR on: {image_path}")
try:
    # When decorated with @tool, it becomes a Tool object.
    # Use .invoke() with a dictionary for arguments
    result = extract_text_from_image.invoke({"image_path": image_path})
    print("--- Result Start ---")
    print(result)
    print("--- Result End ---")
except Exception as e:
    # Try .run() as fallback if invoke doesn't work as expected or for simpler single-arg tools
    try:
        print("Invoke failed or not supported, trying .run()")
        result = extract_text_from_image.run(image_path)
        print("--- Result Start ---")
        print(result)
        print("--- Result End ---")
    except Exception as e2:
        print(f"An error occurred: {e}")
        print(f"Secondary error: {e2}")
