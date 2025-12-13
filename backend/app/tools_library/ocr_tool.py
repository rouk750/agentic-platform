# ocr_tool.py

"""
Tool module for Optical Character Recognition (OCR) on images.
"""

import os
from langchain_core.tools import tool
from PIL import Image
import pytesseract


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
        str: A JSON formatted string. The top level is a list of dictionaries.
             
             Standard keys (light=False):
             - level, page_num, block_num, par_num, line_num, word_num (if 'word')
             - left, top, width, height: Bounding box
             - conf: Confidence (0-100)
             - text: The detected (or grouped) text
             - similarity: (If search_text is used) Fuzzy match score (0-1)
             
             Light keys (light=True):
             - text
             - conf
             - left, top, width, height
             - similarity (If search_text is used)
             
             If no text is found or an error occurs, returns a descriptive message.
    """
    print(
        f"--- Calling tool extract_text_from_image for file "
        f"'{image_path}' with light={light}, group_by='{group_by}', "
        f"search_text='{search_text}' ---"
    )
    import json
    import difflib
    from pytesseract import Output

    try:
        # Expand path to handle aliases like '~'
        expanded_path = os.path.expanduser(image_path)

        if not os.path.isfile(expanded_path):
            return f"Error: The path '{image_path}' is not a valid file."

        # Open image and execute OCR
        image = Image.open(expanded_path)
        
        # Get data including boxes, confidences, line and page numbers
        # Added lang='eng+fra' to basic English + French support for accents
        data = pytesseract.image_to_data(image, output_type=Output.DICT, lang='eng+fra')
        
        num_items = len(data['text'])
        structured_output = []

        # --- helper to process individual item ---
        # We'll normalize data access first
        items = []
        for i in range(num_items):
            item = {k: data[k][i] for k in data.keys()}
            # Basic validation: ensure text is present (even if empty)
            if 'text' not in item:
                item['text'] = ''
            items.append(item)

        # --- Grouping Logic ---
        if group_by == 'word':
            # No grouping (default behavior).
            # We still apply the "skip empty" logic if light=False? 
            # Original code included everything, but let's filter purely empty logic if desired.
            # Usually we iterate and append.
            grouped_items = items
        else:
            # Grouping by 'line' or 'block'
            groups = {}
            for item in items:
                # Key definition for aggregation
                if group_by == 'line':
                    # Unique key for a line: Page, Block, Par, Line
                    key = (item.get('page_num'), item.get('block_num'), 
                           item.get('par_num'), item.get('line_num'))
                elif group_by == 'block':
                    # Unique key for a block/paragraph: Page, Block (, Par?)
                    # Tesseract blocks are usually paragraphs. Par is sometimes sub-paragraph.
                    # Let's stick to Block for broader grouping.
                    key = (item.get('page_num'), item.get('block_num'))
                else:
                    # Fallback to word
                    key = i 

                if key not in groups:
                    groups[key] = {
                        'page_num': item.get('page_num'),
                        'block_num': item.get('block_num'),
                        'par_num': item.get('par_num'),
                        'line_num': item.get('line_num'),
                        'left': item['left'],
                        'top': item['top'],
                        'right': item['left'] + item['width'],
                        'bottom': item['top'] + item['height'],
                        'conf_sum': 0,
                        'conf_count': 0,
                        'text_parts': []
                    }
                
                # Filter meaningless text for aggregation (unless it's word mode)
                txt = item['text']
                if not txt or not txt.strip():
                    continue

                g = groups[key]
                # Update bounding box
                cur_right = item['left'] + item['width']
                cur_bottom = item['top'] + item['height']
                g['left'] = min(g['left'], item['left'])
                g['top'] = min(g['top'], item['top'])
                g['right'] = max(g['right'], cur_right)
                g['bottom'] = max(g['bottom'], cur_bottom)
                
                # Confidence standardizing (tesseract sometimes gives -1 for layout blocks)
                c = int(item['conf'])
                if c >= 0:
                    g['conf_sum'] += c
                    g['conf_count'] += 1
                
                g['text_parts'].append(txt)

            # Reconstruct list from groups
            grouped_items = []
            for k, g in groups.items():
                if not g['text_parts']:
                    continue # Skip empty groups
                
                width = g['right'] - g['left']
                height = g['bottom'] - g['top']
                avg_conf = g['conf_sum'] / g['conf_count'] if g['conf_count'] > 0 else 0
                full_text = " ".join(g['text_parts'])
                
                final_item = {
                    'level': 0, # meaningful level lost in agg
                    'page_num': g['page_num'],
                    'block_num': g['block_num'],
                    'par_num': g['par_num'],
                    'line_num': g['line_num'],
                    'word_num': 0,
                    'left': g['left'],
                    'top': g['top'],
                    'width': width,
                    'height': height,
                    'conf': round(avg_conf),
                    'text': full_text
                }
                grouped_items.append(final_item)


        # --- Light / Search / Final Processing ---
        
        results = []
        light_keys = {'text', 'conf', 'left', 'top', 'width', 'height', 'similarity'}

        for item in grouped_items:
            item_text = item['text']
            
            # Skip empty items (double check)
            if not item_text or not item_text.strip():
                continue

            # Standard light filtering (keys) happens at end. 
            # First, check logic.

            # --- Search Logic ---
            if search_text:
                # Normalize
                s_norm = search_text.lower().strip()
                t_norm = item_text.lower().strip()
                
                if not s_norm:
                    item['similarity'] = 0
                    continue

                # Calculate similarity based on "Query Coverage"
                # Standard ratio() penalizes length differences (e.g. finding a word in a sentence).
                # We want to know: "How much of the search query is in this text?"
                matcher = difflib.SequenceMatcher(None, s_norm, t_norm)
                
                # matching_blocks returns triples (i, j, n)
                # sum(n) gives total characters that matched in order.
                match_size = sum(block.size for block in matcher.get_matching_blocks())
                
                # Coverage score: what % of search text was found?
                # We can also average it with standard ratio if we want to penalize extra text, 
                # but for "search", coverage is usually what matters.
                # However, if target is "a" and search is "abc", coverage is 0.33. Correct.
                # If target is "abc def" and search is "abc", coverage is 1.0. Correct.
                coverage = match_size / len(s_norm) if len(s_norm) > 0 else 0
                
                item['similarity'] = round(coverage, 2)
                
                # Strictly filter low matches
                if coverage < 0.6:
                    continue
            
            # --- Construct Output Item ---
            if light:
                # Filter keys
                final_dict = {k: item[k] for k in item.keys() if k in light_keys}
            else:
                final_dict = item

            results.append(final_dict)

        # Post-loop sort if searching
        if search_text:
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)

        if not results:
             msg = "Information: No data could be extracted"
             if search_text:
                 msg += f" matching '{search_text}'"
             return msg + "."

        return json.dumps(results, indent=2, ensure_ascii=False)

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

