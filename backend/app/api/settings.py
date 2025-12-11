from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models.settings import LLMProfile, ProviderType
from app.schemas.settings import LLMProfileCreate
from app.services.security import save_api_key, delete_api_key, get_api_key
from pydantic import BaseModel
from typing import Optional

# Import LangChain classes for testing connection
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
# Note: For this to work dynamically, we might need more logic, 
# but for US 3.6 we implement a basic switch.

import httpx

router = APIRouter(prefix="/settings", tags=["settings"])

@router.post("/models", response_model=LLMProfile)
def create_model_profile(profile: LLMProfileCreate, session: Session = Depends(get_session)):
    # 1. Save API Key if provided
    key_ref = None
    if profile.api_key:
        key_ref = save_api_key(profile.api_key)
    
    # 2. Save Profile in DB
    db_profile = LLMProfile(
        name=profile.name,
        provider=ProviderType(profile.provider),
        model_id=profile.model_id,
        base_url=profile.base_url,
        api_key_ref=key_ref
    )
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile

@router.get("/models", response_model=List[LLMProfile])
def list_model_profiles(session: Session = Depends(get_session)):
    profiles = session.exec(select(LLMProfile)).all()
    # Explicitly do NOT return the api_key, but LLMProfile model doesn't have it field anyway.
    # The api_key_ref is returned.
    return profiles

@router.delete("/models/{model_id}")
def delete_model_profile(model_id: int, session: Session = Depends(get_session)):
    profile = session.get(LLMProfile, model_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Delete from DB
    session.delete(profile)
    session.commit()
    
    # Delete from Keyring
    if profile.api_key_ref:
        delete_api_key(profile.api_key_ref)
        
    return {"ok": True}

class TestConnectionRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model_id: str
    base_url: Optional[str] = None

from pydantic import BaseModel

@router.post("/test-connection")
async def test_connection(request: TestConnectionRequest):
    try:
        if request.provider == "openai":
            llm = ChatOpenAI(api_key=request.api_key, model=request.model_id, max_tokens=5)
            await llm.ainvoke("test")
        elif request.provider == "anthropic":
            llm = ChatAnthropic(api_key=request.api_key, model=request.model_id, max_tokens=5)
            await llm.ainvoke("test")
        elif request.provider == "ollama":
            # For Ollama, we might check if we can reach the tag endpoint or chat
            # Simple check via httpx
            base_url = request.base_url or "http://localhost:11434"
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{base_url}/api/tags")
                resp.raise_for_status()
        elif request.provider == "lmstudio":
            # For LM Studio, it's openAI compatible.
            # We can try to list models or complete
            base_url = request.base_url or "http://localhost:1234/v1"
            llm = ChatOpenAI(api_key="lm-studio", model=request.model_id, base_url=base_url)
            await llm.ainvoke("test")
        else:
             # Basic fallback or error for unknown providers
             pass
             
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/providers/ollama/scan")
@router.get("/providers/ollama/scan")
async def scan_ollama_models():
    try:
        async with httpx.AsyncClient() as client:
            # Use 127.0.0.1 to avoid ipv6/localhost resolution issues
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                # Extract model names
                models = [model["name"] for model in data.get("models", [])]
                return {"models": models}
            else:
                return {"models": []}
    except Exception:
         return {"models": []} 

@router.get("/providers/lmstudio/scan")
async def scan_lmstudio_models():
    try:
        # LM Studio mimics OpenAI /v1/models
        # Default port 1234
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:1234/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                # data["data"] is a list of objects {id: "...", object: "model", ...}
                models = [model["id"] for model in data.get("data", [])]
                return {"models": models}
            else:
                return {"models": []}
    except Exception:
        return {"models": []} 
