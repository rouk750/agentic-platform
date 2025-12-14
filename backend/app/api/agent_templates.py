from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models.agent_template import AgentTemplate, AgentTemplateVersion
from app.schemas.agent_template import AgentTemplateCreate, AgentTemplateRead, AgentTemplateUpdate, AgentTemplateVersionRead

router = APIRouter()

@router.get("/agent-templates", response_model=List[AgentTemplateRead])
def read_agent_templates(session: Session = Depends(get_session)):
    templates = session.exec(select(AgentTemplate)).all()
    return templates

@router.get("/agent-templates/{template_id}", response_model=AgentTemplateRead)
def read_agent_template(template_id: int, session: Session = Depends(get_session)):
    template = session.get(AgentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Agent Template not found")
    return template

@router.post("/agent-templates", response_model=AgentTemplateRead)
def create_agent_template(template_in: AgentTemplateCreate, session: Session = Depends(get_session)):
    template = AgentTemplate.model_validate(template_in)
    template.created_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    session.refresh(template)
    
    # Create initial version
    version = AgentTemplateVersion(
        template_id=template.id,
        config=template.config,
        created_at=datetime.utcnow(),
        version_number=1
    )
    session.add(version)
    session.commit()
    
    return template

@router.put("/agent-templates/{template_id}", response_model=AgentTemplateRead)
def update_agent_template(template_id: int, template_update: AgentTemplateUpdate, session: Session = Depends(get_session)):
    db_template = session.get(AgentTemplate, template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Agent Template not found")
    
    # Check if config changes to determine if versioning is needed
    should_version = False
    if template_update.config and template_update.config != db_template.config:
        should_version = True
    
    template_data = template_update.model_dump(exclude_unset=True)
    for key, value in template_data.items():
        setattr(db_template, key, value)
    
    db_template.updated_at = datetime.utcnow()
    session.add(db_template)
    session.commit()
    session.refresh(db_template)
    
    if should_version:
        # Get latest version number
        # Logic: find max version number or just count?
        # Let's simple count existing versions + 1, or rely on auto-increment ID if strict numbering isn't required.
        # But user wants neat versions. Let's do a simple count for now.
        existing_versions = session.exec(select(AgentTemplateVersion).where(AgentTemplateVersion.template_id == template_id)).all()
        next_version = len(existing_versions) + 1
        
        version = AgentTemplateVersion(
            template_id=db_template.id,
            config=db_template.config,
            created_at=datetime.utcnow(),
            version_number=next_version
        )
        session.add(version)
        session.commit()
        
    return db_template

@router.delete("/agent-templates/{template_id}")
def delete_agent_template(template_id: int, session: Session = Depends(get_session)):
    template = session.get(AgentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Agent Template not found")
        
    # Manual cascade delete for versions
    versions = session.exec(select(AgentTemplateVersion).where(AgentTemplateVersion.template_id == template_id)).all()
    for v in versions:
        session.delete(v)
        
    session.delete(template)
    session.commit()
    return {"ok": True}

@router.get("/agent-templates/{template_id}/versions", response_model=List[AgentTemplateVersionRead])
def read_agent_template_versions(template_id: int, session: Session = Depends(get_session)):
    template = session.get(AgentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Agent Template not found")
        
    versions = session.exec(select(AgentTemplateVersion).where(AgentTemplateVersion.template_id == template_id).order_by(AgentTemplateVersion.created_at.desc())).all()
    return versions

@router.post("/agent-templates/{template_id}/versions/{version_id}/restore", response_model=AgentTemplateRead)
def restore_agent_template_version(template_id: int, version_id: int, session: Session = Depends(get_session)):
    template = session.get(AgentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Agent Template not found")
        
    version = session.get(AgentTemplateVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    if version.template_id != template_id:
        raise HTTPException(status_code=400, detail="Version does not belong to this template")
        
    template.config = version.config
    template.updated_at = datetime.utcnow()
    
    session.add(template)
    session.commit()
    session.refresh(template)
    return template

@router.delete("/agent-templates/{template_id}/versions/{version_id}")
def delete_agent_template_version(template_id: int, version_id: int, session: Session = Depends(get_session)):
    template = session.get(AgentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Agent Template not found")
        
    version = session.get(AgentTemplateVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    if version.template_id != template_id:
        raise HTTPException(status_code=400, detail="Version does not belong to this template")
        
    session.delete(version)
    session.commit()
    return {"ok": True}
