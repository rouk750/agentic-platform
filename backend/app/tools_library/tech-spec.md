# Backend Tools Library Technical Specification

## Overview
This directory (`backend/app/tools_library`) contains standalone function-based tools compliant with LangChain's `@tool` decorator.

## 1. File Operations

### `read_local_file(file_path: str) -> str`
Reads text content from the local filesystem.
*   **Safety**: Auto-expands `~` user paths. Tries UTF-8 then Latin-1.

### `write_local_file(file_path: str, content: str, overwrite: bool = False) -> str`
Writes text to a file. auto-creates parent directories.
*   **Safety**: Basic path traversal check (unless env var `ALLOW_PATH_TRAVERSAL` is set).

### `read_csv_file(file_path: str) -> str`
Reads a CSV and returns JSON-formatted list of objects.
*   **Logic**: Uses `csv.Sniffer()` to auto-detect delimiters (e.g., semicolon vs comma).

## 2. Vision / OCR

### `extract_text_from_image` (`ocr_tool.py`)
```python
def extract_text_from_image(image_path: str, light: bool = False, group_by: str = 'word', search_text: str = None) -> str
```
Extracts text from images using `Tesseract` (via `pytesseract`).
*   **Args**:
    *   `light` (bool): If True, returns minimal payload (text/conf/pos).
    *   `group_by` (str): 'word' | 'line' | 'block'. Aggregates text spatially.
    *   `search_text` (str): Optional fuzzy search query to rank results.

## 3. Testing

### `fake_tool() -> str`
Returns a static string "iit s a big fake" for testing tool binding paths.
