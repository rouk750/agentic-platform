from app.engine.dspy_utils import get_dspy_lm
from app.models.settings import LLMProfile, ProviderType

def test():
    # Test LM Studio
    p = LLMProfile(id=3, name="LM Studio Local", provider=ProviderType.LMSTUDIO, model_id="local-model-v1")
    try:
        lm = get_dspy_lm(p)
        print("Success: LM Studio LM created:", lm)
        # Check base url if possible
        # print("Base URL:", lm.kwargs.get('api_base')) 
    except Exception as e:
        print("Failed LM Studio:", e)

if __name__ == "__main__":
    test()
