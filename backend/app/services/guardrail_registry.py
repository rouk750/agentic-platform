
from typing import List, Dict, Any

from typing import List, Dict, Any, Callable
from app.engine.dspy_rewards import make_json_reward, make_regex_reward, make_length_reward

# Internal registry mapping ID to definition AND factory
_GUARDRAILS_DB = {
    "json": {
        "def": {
            "id": "json",
            "label": "Enforce JSON Format",
            "description": "Ensures the output is valid JSON.",
            "params": [] 
        },
        "factory": make_json_reward,
        "is_global": True # Special handling for JSON which can be global
    },
    "regex": {
        "def": {
            "id": "regex",
            "label": "Regex Match",
            "description": "Ensures the output matches a specific pattern.",
            "params": [
                {"name": "pattern", "type": "string", "label": "Regex Pattern"}
            ]
        },
        "factory": make_regex_reward,
        "is_global": False
    },
    "length": {
        "def": {
           "id": "length",
            "label": "Max Length",
            "description": "Ensures the output is shorter than a limit.",
            "params": [
                {"name": "max_chars", "type": "number", "label": "Max Characters"}
            ]
        },
        "factory": make_length_reward,
        "is_global": False
    }
}

def get_available_guardrails() -> List[Dict[str, Any]]:
    """Returns the list of public guardrail definitions."""
    return [g["def"] for g in _GUARDRAILS_DB.values()]

def get_guardrail_factory(guardrail_id: str) -> Callable:
    """Returns the factory function for a given guardrail ID."""
    if guardrail_id in _GUARDRAILS_DB:
        return _GUARDRAILS_DB[guardrail_id]["factory"]
    return None
