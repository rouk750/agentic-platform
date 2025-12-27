from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.rag_service import RagService
from app.schemas.chroma_config import ChromaNodeConfig, ChromaMode

router = APIRouter()

# Schema for Test Request
class RagTestRequest(BaseModel):
    query: str
    k: int = 5
    config: ChromaNodeConfig

class RagPreviewRequest(BaseModel):
    config: ChromaNodeConfig
    limit: int = 10
    offset: int = 0

class RagPurgeRequest(BaseModel):
    config: ChromaNodeConfig

@router.post("/preview")
def preview_collection(
    request: RagPreviewRequest
):
    """
    Get a paginated preview of documents in a Chroma collection.
    """
    service = RagService()
    return service.get_collection_preview(
        chroma_config=request.config,
        limit=request.limit,
        offset=request.offset
    )

@router.post("/test")
def test_search(
    request: RagTestRequest
):
    """
    Perform a test search on the collection.
    """
    service = RagService()
    
    # Check simple connectivity first? 
    # The search method handles it.
    
    try:
        # returns string context
        context = service.search(
            query=request.query,
            chroma_config=request.config,
            k=request.k
        )
        return {"result": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/purge")
def purge_collection(
    request: RagPurgeRequest
):
    """
    Purge (delete) a collection.
    """
    service = RagService()
    result = service.delete_collection(request.config)
    if result["status"] == "error":
        # We might not want to 500 if it's just not found, but let's pass message
        return JSONResponse(status_code=400, content=result)
    return result
