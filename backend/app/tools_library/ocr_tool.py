# ocr_tool.py

"""
Tool module for Optical Character Recognition (OCR) on images.
"""

import os
from langchain_core.tools import tool
from PIL import Image
import pytesseract


from .utils import core_ocr_extract

@tool
def extract_text_from_image(image_path: str, light: bool = False, group_by: str = 'word', search_text: str = None) -> str:
    """
    Reads and extracts meaningful data from an image file using OCR.

    This tool returns a JSON string containing detailed information about the
    detected text. It supports grouping by structural elements (line, block)
    and fuzzy search capabilities.

    Args:
        image_path (str): The full path to the image file to analyze
                          (e.g., '~/Desktop/screenshot.png').
        light (bool): If True, returns a lightweight payload optimal for QA/automation.
                      Filters out structural hierarchy and empty text, keeping only:
                      - text, conf, left, top, width, height (and similarity if searching).
        group_by (str): How to aggregate the results. Options:
                        - 'word': No grouping (default). Returns individual words.
                        - 'line': Groups words on the same line.
                        - 'block': Groups words in the same text block (paragraph).
        search_text (str): Optional. If provided, performs a fuzzy search for this text
                           among the results (words or groups). Adds a 'similarity'
                           score (0-1) to each result and sorts by descending score.
                           Results with low similarity may be filtered out.

    Returns:
        str: A JSON formatted string of the extraction results.
    """
    print(
        f"--- Calling tool extract_text_from_image for file "
        f"'{image_path}' with light={light}, group_by='{group_by}', "
        f"search_text='{search_text}' ---"
    )
    return core_ocr_extract(image_path, light, group_by, search_text)


