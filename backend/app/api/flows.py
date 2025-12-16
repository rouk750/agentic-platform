from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
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
    
    # Check if data changes
    should_version = False
    if flow_update.data and flow_update.data != db_flow.data:
        should_version = True

    flow_data = flow_update.model_dump(exclude_unset=True)
    for key, value in flow_data.items():
        setattr(db_flow, key, value)
    
    db_flow.updated_at = datetime.utcnow()
    session.add(db_flow)
    session.commit()
    session.refresh(db_flow)

    if should_version:
        version = FlowVersion(
            flow_id=db_flow.id,
            data=db_flow.data,
            created_at=datetime.utcnow()
        )
        session.add(version)
        session.commit()

    return db_flow

@router.delete("/flows/{flow_id}")
def delete_flow(flow_id: int, session: Session = Depends(get_session)):
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
        
    # Cascade delete versions? SQLModel relationships usually need configuration for cascade.
    # For now, manual delete of versions is safer if relationship isn't set up with cascade.
    versions = session.exec(select(FlowVersion).where(FlowVersion.flow_id == flow_id)).all()
    for v in versions:
        session.delete(v)
        
    session.delete(flow)
    session.commit()
    return {"ok": True}
    
from app.models.flow_version import FlowVersion
from app.schemas.flow_version import FlowVersionRead

@router.get("/flows/{flow_id}/versions", response_model=List[FlowVersionRead])
def read_flow_versions(flow_id: int, session: Session = Depends(get_session)):
    # Check flow exists
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
        
    versions = session.exec(select(FlowVersion).where(FlowVersion.flow_id == flow_id).order_by(FlowVersion.created_at.desc())).all()
    return versions

@router.delete("/flows/{flow_id}/versions/{version_id}")
def delete_flow_version(flow_id: int, version_id: int, session: Session = Depends(get_session)):
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
        
    version = session.get(FlowVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    if version.flow_id != flow_id:
        raise HTTPException(status_code=400, detail="Version does not belong to this flow")
        
    # Check if version is locked
    if version.is_locked:
        raise HTTPException(status_code=400, detail="Cannot delete a locked version")
        
    # Check if version is current (data matches)
    if flow.data == version.data:
        raise HTTPException(status_code=400, detail="Cannot delete the current active version")
        
    session.delete(version)
    session.commit()
    return {"ok": True}

@router.delete("/flows/{flow_id}/versions")
def delete_flow_versions(flow_id: int, version_ids: List[int] = Body(...), session: Session = Depends(get_session)):
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    # Verify all versions belong to the flow and exist
    statement = select(FlowVersion).where(FlowVersion.id.in_(version_ids))
    versions = session.exec(statement).all()
    
    if len(versions) != len(version_ids):
         raise HTTPException(status_code=404, detail="One or more versions not found")

    for version in versions:
        if version.flow_id != flow_id:
             raise HTTPException(status_code=400, detail=f"Version {version.id} does not belong to this flow")
        if version.is_locked:
             raise HTTPException(status_code=400, detail=f"Version {version.id} is locked")
        if flow.data == version.data:
             raise HTTPException(status_code=400, detail=f"Version {version.id} is the current active version")
             
        session.delete(version)
        
    session.commit()
    return {"ok": True}

@router.put("/flows/{flow_id}/versions/{version_id}/lock", response_model=FlowVersionRead)
def toggle_flow_version_lock(
    flow_id: int, 
    version_id: int, 
    is_locked: bool, 
    session: Session = Depends(get_session)
):
    version = session.get(FlowVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    if version.flow_id != flow_id:
        raise HTTPException(status_code=400, detail="Version does not belong to this flow")
        
    version.is_locked = is_locked
    session.add(version)
    session.commit()
    session.refresh(version)
    return version

@router.post("/flows/{flow_id}/versions/{version_id}/restore", response_model=FlowRead)
def restore_flow_version(flow_id: int, version_id: int, session: Session = Depends(get_session)):
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
        
    version = session.get(FlowVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    if version.flow_id != flow_id:
        raise HTTPException(status_code=400, detail="Version does not belong to this flow")
        
    # Update flow with version data
    flow.data = version.data
    # Also unarchive if restoring? Let's keep it simple for now, user manually unarchives.
    flow.updated_at = datetime.utcnow()
    
    session.add(flow)
    session.commit()
    session.refresh(flow)
    return flow
