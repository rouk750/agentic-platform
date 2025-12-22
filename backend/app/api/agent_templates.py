"""
AgentTemplate API Routes

RESTful API endpoints for AgentTemplate CRUD operations.
Uses AgentTemplateService for business logic.
"""

from typing import List
from fastapi import APIRouter, Depends, Body
from sqlmodel import Session

from app.database import get_session
from app.schemas.agent_template import (
    AgentTemplateCreate,
    AgentTemplateRead,
    AgentTemplateUpdate,
    AgentTemplateVersionRead,
)
from app.services.template_service import AgentTemplateService

router = APIRouter()


def get_template_service(session: Session = Depends(get_session)) -> AgentTemplateService:
    """Dependency injection for AgentTemplateService."""
    return AgentTemplateService(session)


# Template CRUD

@router.get("/agent-templates", response_model=List[AgentTemplateRead])
def read_agent_templates(
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 100,
    service: AgentTemplateService = Depends(get_template_service)
):
    """List all agent templates with optional pagination."""
    return service.list_templates(skip=skip, limit=limit, include_archived=include_archived)


@router.get("/agent-templates/{template_id}", response_model=AgentTemplateRead)
def read_agent_template(
    template_id: int,
    service: AgentTemplateService = Depends(get_template_service)
):
    """Get a single template by ID."""
    return service.get_template(template_id)


@router.post("/agent-templates", response_model=AgentTemplateRead)
def create_agent_template(
    template_in: AgentTemplateCreate,
    service: AgentTemplateService = Depends(get_template_service)
):
    """Create a new agent template with initial version."""
    return service.create_template(template_in)


@router.put("/agent-templates/{template_id}", response_model=AgentTemplateRead)
def update_agent_template(
    template_id: int,
    template_update: AgentTemplateUpdate,
    service: AgentTemplateService = Depends(get_template_service)
):
    """Update a template. Creates version if config changes."""
    return service.update_template(template_id, template_update)


@router.delete("/agent-templates/{template_id}")
def delete_agent_template(
    template_id: int,
    service: AgentTemplateService = Depends(get_template_service)
):
    """Delete a template and all its versions."""
    service.delete_template(template_id)
    return {"ok": True}


# Version Management

@router.get("/agent-templates/{template_id}/versions", response_model=List[AgentTemplateVersionRead])
def read_agent_template_versions(
    template_id: int,
    service: AgentTemplateService = Depends(get_template_service)
):
    """List all versions for a template."""
    return service.list_versions(template_id)


@router.delete("/agent-templates/{template_id}/versions/{version_id}")
def delete_agent_template_version(
    template_id: int,
    version_id: int,
    service: AgentTemplateService = Depends(get_template_service)
):
    """Delete a single version."""
    service.delete_version(template_id, version_id)
    return {"ok": True}


@router.delete("/agent-templates/{template_id}/versions")
def delete_agent_template_versions(
    template_id: int,
    version_ids: List[int] = Body(...),
    service: AgentTemplateService = Depends(get_template_service)
):
    """Bulk delete multiple versions."""
    for vid in version_ids:
        service.delete_version(template_id, vid)
    return {"ok": True}


@router.put("/agent-templates/{template_id}/versions/{version_id}/lock", response_model=AgentTemplateVersionRead)
def toggle_agent_template_version_lock(
    template_id: int,
    version_id: int,
    is_locked: bool,
    service: AgentTemplateService = Depends(get_template_service)
):
    """Lock or unlock a version."""
    return service.toggle_version_lock(template_id, version_id, is_locked)


@router.post("/agent-templates/{template_id}/versions/{version_id}/restore", response_model=AgentTemplateRead)
def restore_agent_template_version(
    template_id: int,
    version_id: int,
    service: AgentTemplateService = Depends(get_template_service)
):
    """Restore template to a previous version."""
    return service.restore_version(template_id, version_id)
