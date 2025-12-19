# pdf_tool.py

"""
Tool module for extracting content from PDF files using multiple strategies.
Designed to handle variable formats like Financial Reports.
"""

import os
import json
import tempfile
from typing import Optional, List
from langchain_core.tools import tool

# Attempt to import dependencies
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pdf2image
except ImportError:
    pdf2image = None

# Import shared OCR logic
from .utils import core_ocr_extract

@tool
def extract_pdf_content(file_path: str, strategy: str = "auto", pages: str = None, image_output_mode: str = "path", vertical_splits: int = 1) -> str:
    """
    Extracts text and structure from a PDF file using the specified strategy.

    Strategies:
    - 'fast': pypdf text extraction.
    - 'ocr_vision': Local OCR (Tesseract).
    - 'vision_llm': Returns image paths or base64 for Multimodal Models.
    
    Args:
        file_path (str): Absolute path to the PDF file.
        strategy (str): 'auto', 'fast', 'ocr_vision', 'vision_llm'.
        pages (str, optional): Comma-separated list of page numbers (0-indexed).
        image_output_mode (str, optional): 'path' (default) or 'base64'. Used with 'vision_llm'.
        vertical_splits (int, optional): Number of vertical sections to split each page into.
                                         Default is 1 (no split).
                                         Useful to reduce per-image token count or strict resolution limits.
                                         e.g., 2 will split page into Top Half and Bottom Half.

    Returns:
        str: JSON string containing extracted content per page (or per chunk).
    """
    import base64

    print(f"--- Calling tool extract_pdf_content for '{file_path}' with strategy='{strategy}' splits={vertical_splits} ---")

    # ... (Validation code same as before, skipping for brevity in replacement if unchanged, but I must match target) ...
    # To avoid repeating 100 lines of unchanged code, I will use precise context targeting for signature and then the loop.

    # 1. Validation
    expanded_path = os.path.expanduser(file_path)
    if not os.path.isfile(expanded_path):
        return f"Error: File not found at {expanded_path}"

    if not expanded_path.lower().endswith('.pdf'):
        return "Error: File is not a PDF."

    # Decide strategy
    if strategy == "auto":
        strategy = "fast"

    # Parse pages
    pages_list = None
    if pages:
        try:
            pages_list = [int(p.strip()) for p in pages.split(',') if p.strip()]
        except ValueError:
            return "Error: 'pages' must be a comma-separated list of integers (e.g., '0,2')."

    results = []

    try:
        # STRATEGY: FAST
        if strategy == "fast":
            # ... (fast impl) ...
            if not pypdf:
                return "Error: 'pypdf' library not installed."
            
            reader = pypdf.PdfReader(expanded_path)
            total_pages = len(reader.pages)
            pages_to_process = pages_list if pages_list else range(total_pages)

            for i in pages_to_process:
                if 0 <= i < total_pages:
                    text = reader.pages[i].extract_text()
                    results.append({
                        "page_num": i + 1,
                        "strategy": "fast",
                        "content": text
                    })
            return json.dumps(results, indent=2, ensure_ascii=False)

        # STRATEGY: VISION / OCR
        elif strategy in ["ocr_vision", "vision_llm"]:
            if not pdf2image:
                return "Error: 'pdf2image' library not installed."

            # Dir Setup
            if strategy == "vision_llm":
                base_dir = os.path.join(tempfile.gettempdir(), "agent_vision_cache")
                os.makedirs(base_dir, exist_ok=True)
                temp_context = None 
                storage_dir = base_dir
            else:
                temp_context = tempfile.TemporaryDirectory()
                storage_dir = temp_context.name

            try:
                # Convert Pages
                if pages_list:
                    images_info = []
                    for p_idx in pages_list:
                        imgs = pdf2image.convert_from_path(expanded_path, first_page=p_idx+1, last_page=p_idx+1)
                        if imgs:
                            images_info.append((p_idx, imgs[0]))
                else:
                    pil_images = pdf2image.convert_from_path(expanded_path)
                    images_info = [(i, img) for i, img in enumerate(pil_images)]

                vision_results = []

                for p_idx, pil_image in images_info:
                    
                    # Handle Splitting
                    width, height = pil_image.size
                    
                    # Ensure at least 1 split
                    num_splits = max(1, vertical_splits)
                    section_height = height // num_splits

                    for split_idx in range(num_splits):
                        
                        # Define Crop Box (left, upper, right, lower)
                        if num_splits > 1:
                            upper = split_idx * section_height
                            # For last chunk, take remaining height to avoid pixel loss
                            lower = (split_idx + 1) * section_height if split_idx < num_splits - 1 else height
                            
                            crop_img = pil_image.crop((0, upper, width, lower))
                            chunk_suffix = f"_part{split_idx+1}of{num_splits}"
                        else:
                            crop_img = pil_image
                            chunk_suffix = ""

                        # Save
                        filename = f"{os.path.basename(file_path)}_{p_idx}{chunk_suffix}.png"
                        img_path = os.path.join(storage_dir, filename)
                        crop_img.save(img_path, "PNG")

                        # Output Generation
                        if strategy == "vision_llm":
                            item = {
                                "page_num": p_idx + 1,
                                "strategy": "vision_llm",
                                "split_index": split_idx + 1,
                                "total_splits": num_splits,
                                "info": "Image prepared for Vision Model."
                            }
                            
                            if image_output_mode == "base64":
                                with open(img_path, "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                                item["image_base64"] = encoded_string
                            else:
                                item["image_path"] = img_path
                            
                            vision_results.append(item)

                        else:
                            # OCR Vision (supports splitting too, though less common)
                            ocr_result_json = core_ocr_extract(img_path, light=False, group_by='block')
                            ocr_data = json.loads(ocr_result_json) if not ocr_result_json.startswith("Error") else ocr_result_json
                            
                            vision_results.append({
                                "page_num": p_idx + 1,
                                "strategy": "ocr_vision",
                                "split_index": split_idx + 1,
                                "total_splits": num_splits,
                                "raw_ocr_data": ocr_data
                            })
                
                return json.dumps(vision_results, indent=2, ensure_ascii=False)

            except Exception as e:
                if "poppler" in str(e).lower():
                        return "Error: Poppler is not installed or not in PATH."
                raise e
            finally:
                if temp_context:
                    temp_context.cleanup()



        else:
            return f"Error: Unknown strategy '{strategy}'."

    except Exception as e:
        return f"Unexpected error processing PDF: {e}"
