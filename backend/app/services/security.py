import keyring
import uuid
from typing import Optional

SERVICE_NAME = "AgentArchitectApp"

def save_api_key(api_key: str) -> str:
    """Sauvegarde la clé et retourne son ID de référence"""
    key_ref = str(uuid.uuid4())
    keyring.set_password(SERVICE_NAME, key_ref, api_key)
    return key_ref

def get_api_key(key_ref: str) -> Optional[str]:
    try:
        return keyring.get_password(SERVICE_NAME, key_ref)
    except Exception:
        return None

def delete_api_key(key_ref: str):
    try:
        keyring.delete_password(SERVICE_NAME, key_ref)
    except Exception:
        pass # Ignore if key not found
