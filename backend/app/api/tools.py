from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

@router.get("/tools", response_model=List[Dict[str, str]])
async def list_tools():
    """
    List available tools that can be used in the graph.
    Scans the backend/app/tools_library directory.
    """
    from app.services.tool_registry import list_tools_metadata
    return await list_tools_metadata()
