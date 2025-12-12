from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.schemas.settings import LLMProfileCreate # Assuming we might reuse or just ID

class DSPyExample(BaseModel):
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]

class OptimizationRequest(BaseModel):
    node_id: str
    goal: str
    mode: str # "ChainOfThought" or "Predict"
    inputs: List[Dict[str, Any]] # List of {name, desc}
    outputs: List[Dict[str, Any]] # List of {name, desc}
    examples: List[DSPyExample]
    llm_profile_id: int
    metric: str = "semantic" # "exact_match" or "semantic"
    max_rounds: Optional[int] = 10

class OptimizationResponse(BaseModel):
    status: str
    compiled_program_path: str
    score: float
