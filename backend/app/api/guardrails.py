
from fastapi import APIRouter
from app.services.guardrail_registry import get_available_guardrails

router = APIRouter()

@router.get("/guardrails")
async def list_guardrails():
    """
    Returns the list of available guardrails and their configuration parameters.
    """
    return get_available_guardrails()
