# ocr_tool.py

"""
Tool module for Optical Character Recognition (OCR) on images.
"""

import os
from langchain_core.tools import tool
from PIL import Image
import pytesseract


@tool
def extract_text_from_image(image_path: str) -> str:
    """
    Reads and extracts meaningful data from an image file using OCR.

    This tool returns a JSON string containing detailed information about the
    detected text, including its position, confidence level, and structural
    hierarchy (page, block, paragraph, line, word).

    Args:
        image_path (str): The full path to the image file to analyze
                          (e.g., '~/Desktop/screenshot.png').

    Returns:
        str: A JSON formatted string. The top level is a list of dictionaries,
             where each dictionary represents a detected element with keys:
             - level: Hierarchical level
             - page_num: Page number
             - block_num: Block number
             - par_num: Paragraph number
             - line_num: Line number
             - word_num: Word number
             - left: X coordinate (pixels)
             - top: Y coordinate (pixels)
             - width: Width (pixels)
             - height: Height (pixels)
             - conf: Confidence (0-100)
             - text: The detected text
             
             If no text is found or an error occurs, returns a descriptive message.
    """
    print(
        f"--- Calling tool extract_text_from_image for file "
        f"'{image_path}' ---"
    )
    import json
    from pytesseract import Output

    try:
        # Expand path to handle aliases like '~'
        expanded_path = os.path.expanduser(image_path)

        if not os.path.isfile(expanded_path):
            return f"Error: The path '{image_path}' is not a valid file."

        # Open image and execute OCR
        image = Image.open(expanded_path)
        
        # Get data including boxes, confidences, line and page numbers
        data = pytesseract.image_to_data(image, output_type=Output.DICT)
        
        # The result 'data' is a dict of lists {key: [val1, val2, ...]}
        # We want to convert this to a list of dicts [{key: val1}, {key: val2}, ...]
        # efficiently.
        
        keys = data.keys()
        num_items = len(data['text'])
        structured_output = []

        for i in range(num_items):
            # perform a basic filter to only keep items with actual text or relevant structure if needed
            # usually empty text means it's a structural element or whitespace.
            # We include everything for completeness as requested, or filter?
            # User asked for "data", usually implies full detail, but empty text entries 
            # are often just layout blocks. Let's filter out completely empty text entries 
            # to keep it cleaner, unless they have high confidence (which they usually don't).
            # Tesseract often returns empty strings for structural blocks.
            
            # Let's keep it raw but maybe just filter out truly empty recognition if conf is -1 (which acts as header/block marker)
            # Actually, standard image_to_data returns conf -1 for higher level structure blocks.
            
            item = {k: data[k][i] for k in keys}
            structured_output.append(item)

        if not structured_output:
             return "Information: No data could be extracted from the image."

        return json.dumps(structured_output, indent=2)

    except FileNotFoundError:
        return f"Error: The file '{image_path}' was not found."
    except Image.UnidentifiedImageError:
        return (
            f"Error: The file '{image_path}' is not a recognized "
            f"image format."
        )
    except pytesseract.TesseractNotFoundError:
        return (
            "Critical error: The Tesseract executable is not installed "
            "or is not in the system PATH. The OCR tool cannot "
            "function."
        )
    except Exception as e:
        return (
            f"Unexpected error while processing image "
            f"'{image_path}': {e}"
        )

