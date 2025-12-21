import re
import json
from typing import Optional, Dict

def sanitize_label(label: str) -> str:
    """
    Sanitizes a label string to be safe for use as a tool name or ID.
    Replaces non-alphanumeric characters (except underscore and hyphen) with underscores.
    """
    if not label:
        return ""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', label)

def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Attempts to extract a JSON object from a string.
    Useful for interacting with LLMs that output JSON inside code blocks or mixed text.
    """
    if not text:
        return None
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    # Try finding JSON block {}
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Try finding Markdown JSON block ```json ... ```
    match_md = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match_md:
         try:
            return json.loads(match_md.group(1))
         except json.JSONDecodeError:
            pass

    return None

def render_template(template: str, context: Dict) -> str:
    """
    Renders a simple template string with {{ variable }} syntax.
    Replaces missing variables with <VARIABLE NOT FOUND>.
    """
    if not template or not context:
        return template
        
    pattern = r"\{\{\s*(\w+)\s*\}\}"
    
    def replace_match(match):
        var_name = match.group(1)
        if var_name in context:
            return str(context[var_name])
        return f"<{var_name} NOT FOUND>"

    return re.sub(pattern, replace_match, template)
