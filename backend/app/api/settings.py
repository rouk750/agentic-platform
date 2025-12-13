from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models.settings import LLMProfile, ProviderType
from app.schemas.settings import LLMProfileCreate, LLMProfileUpdate
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

@router.put("/models/{model_id}", response_model=LLMProfile)
def update_model_profile(model_id: int, profile_update: LLMProfileUpdate, session: Session = Depends(get_session)):
    db_profile = session.get(LLMProfile, model_id)
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile_update.name is not None:
        db_profile.name = profile_update.name
    if profile_update.provider is not None:
        db_profile.provider = ProviderType(profile_update.provider)
    if profile_update.model_id is not None:
        db_profile.model_id = profile_update.model_id
    if profile_update.base_url is not None:
        db_profile.base_url = profile_update.base_url
    
    # Handle API Key rotation
    if profile_update.api_key:
        # Delete old key if exists
        if db_profile.api_key_ref:
            delete_api_key(db_profile.api_key_ref)
        # Save new key
        db_profile.api_key_ref = save_api_key(profile_update.api_key)
    
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile

@router.post("/models/{model_id}/test")
async def test_saved_model_connection(model_id: int, session: Session = Depends(get_session)):
    profile = session.get(LLMProfile, model_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        from app.providers.factory import LLMProviderFactory
        provider = LLMProviderFactory.get_provider(profile.provider)
        
        # Retrieve API key if reference exists
        api_key = None
        if profile.api_key_ref:
            api_key = get_api_key(profile.api_key_ref)
            
        await provider.test_connection(profile, api_key=api_key)
        return {"status": "ok"}
    except Exception as e:
        # import traceback
        # traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

class TestConnectionRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model_id: str
    base_url: Optional[str] = None

from pydantic import BaseModel

@router.post("/test-connection")
async def test_connection(request: TestConnectionRequest):
    try:
        # Create a temporary profile object
        # We need to map the string provider to the Enum.
        try:
            provider_type = ProviderType(request.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown provider {request.provider}")

        temp_profile = LLMProfile(
             name="temp",
             provider=provider_type,
             model_id=request.model_id,
             base_url=request.base_url,
             temperature=0.0
        )
        
        from app.providers.factory import LLMProviderFactory
        provider = LLMProviderFactory.get_provider(provider_type)
        await provider.test_connection(temp_profile, api_key=request.api_key)

        return {"status": "ok"}
    except Exception as e:
        import traceback
        traceback.print_exc()
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
