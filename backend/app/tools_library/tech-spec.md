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

### `extract_pdf_content` (`pdf_tool.py`)
```python
def extract_pdf_content(file_path: str, strategy: str = "auto", pages: str = None, image_output_mode: str = "path", vertical_splits: int = 1) -> str
```
Extracts content from PDF.
*   **Strategies**:
    *   `fast`: Text extraction (pypdf).
    *   `vision_llm`: Converts pages to images (JPEG 95, Data URI output if base64 requested).
*   **Args**:
    *   `image_output_mode`: 'path' (default) or 'base64'.
    *   `vertical_splits`: Horizontal splitting for token optimization.

## 2. Vision / OCR

### `extract_text_from_image` (`ocr_tool.py`)
```python
def extract_text_from_image(image_path: str, light: bool = False, group_by: str = 'word', search_text: str = None) -> str
```
Extracts text from images using `Tesseract` (via `pytesseract`).
*   **Args**:
    *   `light` (bool): If True, returns minimal payload (text/conf/pos).
    *   `group_by` (str): 'word' | 'line' | 'block'. Aggregates text spatially.
    *   `group_by` (str): 'word' | 'line' | 'block'. Aggregates text spatially.
    *   `search_text` (str): Optional fuzzy search query to rank results.

### `read_image` (`image_reader.py`)
```python
def read_image(image_path: str) -> str
```
Reads a local image and converts it to Base64 Data URI.
*   **Purpose**: Enabling Vision Agents to "see" local files.
*   **Optimization**: Resizes to max 1920px and converts to JPEG (Quality 95) to prevent Context Limit explosion (Ollama compatible).
*   **Output**: `data:image/jpeg;base64,...` string.


