import dspy
import keyring
from app.models.settings import LLMProfile, ProviderType

def get_dspy_lm(profile: LLMProfile) -> dspy.LM:
    """
    Factory to create a DSPy LM client from an LLMProfile.
    Uses the unified dspy.LM interface (DSPy 2.5/3.0+).
    """
    api_key = None
    if profile.api_key_ref:
        api_key = keyring.get_password("agentic-platform", profile.api_key_ref)
    
    # Ensure a dummy key is present if None, as some clients validate this
    safe_key = api_key or "sk-dummy"

    # 1. Determine Provider Prefix & Config
    model_path = profile.model_id or ""
    kwargs = {"api_key": safe_key}
    
    if profile.provider == ProviderType.OPENAI:
        # e.g. "openai/gpt-4"
        if not model_path.startswith("openai/"):
            model_path = f"openai/{model_path}"
        if profile.base_url:
            kwargs["api_base"] = profile.base_url

    elif profile.provider == ProviderType.ANTHROPIC:
        # e.g. "anthropic/claude-3-opus"
        if not model_path.startswith("anthropic/"):
            model_path = f"anthropic/{model_path}"
        # Anthropic in DSPy might use different config keys, but LM is usually consistent
    
    elif profile.provider == ProviderType.OLLAMA:
        # e.g. "ollama_chat/llama3"
        # Important: DSPy often requires 'ollama_chat/' for chat models or just 'ollama/'
        # We will assume chat for smart nodes
        clean_model = model_path.replace("ollama/", "").replace("ollama_chat/", "")
        model_path = f"ollama_chat/{clean_model}"
        
        # Local URL
        base_url = profile.base_url or "http://localhost:11434"
        kwargs["api_base"] = base_url
        kwargs["api_key"] = "" # Ollama doesn't need key
    
    elif profile.provider == ProviderType.AZURE:
         # e.g. "azure/deployment-name"
         if not model_path.startswith("azure/"):
            model_path = f"azure/{model_path}"
         if profile.base_url:
            kwargs["api_base"] = profile.base_url
            
    elif profile.provider == ProviderType.LMSTUDIO:
         # e.g. "lmstudio/model-name" -> treat as openai compatible
         # LM Studio usually runs on port 1234
         if not model_path.startswith("openai/"):
            model_path = f"openai/{model_path}"
         
         url = profile.base_url if profile.base_url else "http://localhost:1234/v1"
         if not url.endswith("/v1"):
            url = f"{url}/v1"
            
         kwargs["api_base"] = url
         kwargs["api_key"] = "lm-studio"
            
    else:
        # Fallback treat as openai compatible
        if not model_path.startswith("openai/"):
            model_path = f"openai/{model_path}"
        if profile.base_url:
            kwargs["api_base"] = profile.base_url

    # 2. Instantiate dspy.LM
    # print(f"Initializing DSPy LM: {model_path} with base {kwargs.get('api_base')}")
    try:
        return dspy.LM(model_path, **kwargs)
    except Exception as e:
        print(f"Error initializing dspy.LM for {model_path}: {e}")
        # Fallback attempt without prefix if it failed? 
        # Or re-raise. Better to fail loudly now.
        raise e
