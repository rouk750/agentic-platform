from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models.flow import Flow
from app.schemas.flow import FlowCreate, FlowRead, FlowUpdate

router = APIRouter()

@router.get("/flows", response_model=List[FlowRead])
def read_flows(session: Session = Depends(get_session)):
    flows = session.exec(select(Flow)).all()
    return flows

@router.get("/flows/{flow_id}", response_model=FlowRead)
def read_flow(flow_id: int, session: Session = Depends(get_session)):
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow

@router.post("/flows", response_model=FlowRead)
def create_flow(flow_in: FlowCreate, session: Session = Depends(get_session)):
    flow = Flow.model_validate(flow_in) # Convert schema to model
    flow.created_at = datetime.utcnow()
    flow.updated_at = datetime.utcnow()
    session.add(flow)
    session.commit()
    session.refresh(flow)
    return flow

@router.put("/flows/{flow_id}", response_model=FlowRead)
def update_flow(flow_id: int, flow_update: FlowUpdate, session: Session = Depends(get_session)):
    db_flow = session.get(Flow, flow_id)
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    flow_data = flow_update.model_dump(exclude_unset=True)
    for key, value in flow_data.items():
        setattr(db_flow, key, value)
    
    db_flow.updated_at = datetime.utcnow()
    session.add(db_flow)
    session.commit()
    session.refresh(db_flow)
    return db_flow

@router.delete("/flows/{flow_id}")
def delete_flow(flow_id: int, session: Session = Depends(get_session)):
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    session.delete(flow)
    session.commit()
    return {"ok": True}
