from app.engine.dspy_utils import get_dspy_lm
from app.models.settings import LLMProfile, ProviderType

def test():
    # Test Ollama
    p = LLMProfile(id=1, name="Ollama Test", provider=ProviderType.OLLAMA, model_id="llama3")
    try:
        lm = get_dspy_lm(p)
        print("Success: Ollama LM created:", lm)
    except Exception as e:
        print("Failed Ollama:", e)

    # Test OpenAI
    p2 = LLMProfile(id=2, name="OpenAI Test", provider=ProviderType.OPENAI, model_id="gpt-4o")
    try:
        lm2 = get_dspy_lm(p2)
        print("Success: OpenAI LM created:", lm2)
    except Exception as e:
        print("Failed OpenAI:", e)

if __name__ == "__main__":
    test()
