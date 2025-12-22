import base64
import os
import io
import mimetypes
from langchain_core.tools import tool
from PIL import Image

@tool
def read_image(image_path: str, max_dimension: int = 1920) -> str:
    """
    Reads a local image file, resizes it to fit within max_dimension (maintaining aspect ratio),
    and converts it to a base64 Data URI string.
    
    Resizing is CRITICAL for local models (Ollama) to avoid exceeding context limits.
    A raw 1080p screenshot can easily consume 500k+ tokens.

    Args:
        image_path (str): The full path to the image file (e.g. '~/Desktop/chart.png').
        max_dimension (int): Max width or height in pixels. Default is 2048.

    Returns:
        str: A Data URI string (e.g., 'data:image/jpeg;base64,...').
    """
    try:
        # Sanitize and expand path
        clean_path = image_path.strip().strip("'").strip('"')
        clean_path = os.path.expanduser(clean_path)

        if not os.path.exists(clean_path):
            return f"Error: Image file not found at {clean_path}"

        # 1. Open Image with PIL
        try:
            with Image.open(clean_path) as img:
                # 2. Convert to RGB (handles RGBA/P mimes correctly for saving as JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                    
                # 3. Calculate new size
                width, height = img.size
                
                # [Optimization] Adjusted to 1920 (Full HD).
                # 2048px was pushing limits, 1024px was too blurry used 1920 as sweet spot.
                if max(width, height) > max_dimension:
                    scale_factor = max_dimension / max(width, height)
                    new_size = (int(width * scale_factor), int(height * scale_factor))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 4. Save to Bytes
                # Use High Quality JPEG (95) to avoid artifacts on text.
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=95)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                return f"data:image/jpeg;base64,{img_str}"

        except Exception as e:
            return f"Error processing image with PIL: {str(e)}"

    except Exception as e:
        return f"Error reading image: {str(e)}"
