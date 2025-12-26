"""
Flow API Routes

RESTful API endpoints for Flow CRUD operations.
Uses FlowService for business logic.
"""

from typing import List
from fastapi import APIRouter, Depends, Body
from sqlmodel import Session

from app.database import get_session
from app.schemas.flow import FlowCreate, FlowRead, FlowUpdate
from app.schemas.flow_version import FlowVersionRead
from app.services.flow_service import FlowService

router = APIRouter()


def get_flow_service(session: Session = Depends(get_session)) -> FlowService:
    """Dependency injection for FlowService."""
    return FlowService(session)


# Flow CRUD

@router.get("/flows", response_model=List[FlowRead])
def read_flows(
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 100,
    service: FlowService = Depends(get_flow_service)
):
    """List all flows with optional pagination and archive filter."""
    return service.list_flows(skip=skip, limit=limit, include_archived=include_archived)


@router.get("/flows/{flow_id}", response_model=FlowRead)
def read_flow(flow_id: int, service: FlowService = Depends(get_flow_service)):
    """Get a single flow by ID."""
    return service.get_flow(flow_id)


@router.post("/flows", response_model=FlowRead)
def create_flow(flow_in: FlowCreate, service: FlowService = Depends(get_flow_service)):
    """Create a new flow."""
    return service.create_flow(flow_in)


@router.put("/flows/{flow_id}", response_model=FlowRead)
def update_flow(
    flow_id: int,
    flow_update: FlowUpdate,
    service: FlowService = Depends(get_flow_service)
):
    """Update a flow. Creates version if data changes."""
    return service.update_flow(flow_id, flow_update)


@router.delete("/flows/{flow_id}")
def delete_flow(flow_id: int, service: FlowService = Depends(get_flow_service)):
    """Delete a flow and all its versions."""
    service.delete_flow(flow_id)
    return {"ok": True}


# Version Management

@router.get("/flows/{flow_id}/versions", response_model=List[FlowVersionRead])
def read_flow_versions(flow_id: int, service: FlowService = Depends(get_flow_service)):
    """List all versions for a flow."""
    return service.list_versions(flow_id)


@router.delete("/flows/{flow_id}/versions/{version_id}")
def delete_flow_version(
    flow_id: int,
    version_id: int,
    service: FlowService = Depends(get_flow_service)
):
    """Delete a single version."""
    service.delete_version(flow_id, version_id)
    return {"ok": True}


@router.delete("/flows/{flow_id}/versions")
def delete_flow_versions(
    flow_id: int,
    version_ids: List[int] = Body(...),
    service: FlowService = Depends(get_flow_service)
):
    """Bulk delete multiple versions."""
    for vid in version_ids:
        service.delete_version(flow_id, vid)
    return {"ok": True}


@router.put("/flows/{flow_id}/versions/{version_id}/lock", response_model=FlowVersionRead)
def toggle_flow_version_lock(
    flow_id: int,
    version_id: int,
    is_locked: bool,
    service: FlowService = Depends(get_flow_service)
):
    """Lock or unlock a version."""
    return service.toggle_version_lock(flow_id, version_id, is_locked)


@router.post("/flows/{flow_id}/versions/{version_id}/restore", response_model=FlowRead)
def restore_flow_version(
    flow_id: int,
    version_id: int,
    service: FlowService = Depends(get_flow_service)
):
    """Restore flow to a previous version."""
    return service.restore_version(flow_id, version_id)
