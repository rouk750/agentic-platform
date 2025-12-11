from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.schemas.dspy_schema import OptimizationRequest, OptimizationResponse
from app.engine.dspy_optimizer import optimize_node
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/smart-nodes/optimize", response_model=OptimizationResponse)
async def optimize_smart_node(request: OptimizationRequest, session: Session = Depends(get_session)):
    try:
        response = await optimize_node(request, session)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
