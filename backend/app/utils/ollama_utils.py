from typing import List
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage

def adjust_messages_for_ollama(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Adjusts a list of messages to be compatible with Ollama's vision capabilities.
    
    Problem:
    Ollama (via LangChain) often treats Base64 image data in ToolMessages as raw text,
    causing context window explosions. It natively expects images to be associated 
    with User (Human) messages to trigger the Vision Encoder.

    Solution:
    This function scans for ToolMessages containing images (either as structured list 
    or raw Base64 string) and converts them into HumanMessages with the correct 
    multimodal structure: [{"type": "text", ...}, {"type": "image_url", ...}].

    Args:
        messages (List[BaseMessage]): The original conversation history.

    Returns:
        List[BaseMessage]: A new list of messages where image-containing ToolMessages 
                           are converted to HumanMessages.
    """
    adjusted_messages = []
    for m in messages:
        if isinstance(m, ToolMessage):
            # Case 1: Already structured as list (Multi-modal)
            if isinstance(m.content, list):
                # Check for image_url
                has_image = any(isinstance(block, dict) and block.get('type') == 'image_url' for block in m.content)
                if has_image:
                    # Convert to HumanMessage to force vision processing
                    adjusted_messages.append(HumanMessage(content=m.content, name=m.name))
                else:
                    adjusted_messages.append(m)
            
            # Case 2: String content (Standard ToolNode output) containing Base64 Image
            elif isinstance(m.content, str) and m.content.strip().startswith("data:image/"):
                # Convert raw string to structured image content
                new_content = [
                    {"type": "text", "text": "Tool Output: Image successfully loaded:"},
                    {"type": "image_url", "image_url": {"url": m.content}}
                ]
                adjusted_messages.append(HumanMessage(content=new_content, name=m.name))
            else:
                adjusted_messages.append(m)
        else:
            adjusted_messages.append(m)
            
    return adjusted_messages
