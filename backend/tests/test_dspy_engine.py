import pytest
import dspy
from app.engine.dspy_utils import get_dspy_lm
from app.models.settings import LLMProfile, ProviderType

# --- LM Factory Tests ---

def test_get_dspy_lm_ollama():
    """Verify Ollama LM creation via dspy.LM adapter."""
    p = LLMProfile(id=1, name="Ollama Test", provider=ProviderType.OLLAMA, model_id="llama3")
    lm = get_dspy_lm(p)
    assert lm is not None
    # Check if model string is correctly formatted (usually "ollama_chat/llama3" or similar)
    # The adapter might prefix it or handle it internally.
    # DSPy 3.0 uses 'model' attribute usually.
    assert "llama3" in lm.model

def test_get_dspy_lm_openai():
    """Verify OpenAI LM creation."""
    p = LLMProfile(id=2, name="OpenAI Test", provider=ProviderType.OPENAI, model_id="gpt-4o")
    lm = get_dspy_lm(p)
    assert lm is not None
    assert "gpt-4o" in lm.model

def test_get_dspy_lm_lmstudio():
    """Verify LM Studio configuration (local OpenAI compatible)."""
    p = LLMProfile(id=3, name="LM Studio Local", provider=ProviderType.LMSTUDIO, model_id="local-model-v1")
    lm = get_dspy_lm(p)
    assert lm is not None
    # Verify that base_url is correctly passed if dspy.LM exposes it, 
    # or at least that it didn't crash.
    # For LM Studio, we expect a default base_url to be set in dspy_utils if not provided.
    
# --- Signature Tests ---

def test_dspy_make_signature_v3():
    """Verify that dspy.make_signature works with the dictionary syntax (v2.5/3.0+)."""
    # Specifically testing the {name: Field} syntax which was causing issues before.
    fields_simple = {
        "question": dspy.InputField(desc="The question"),
        "answer": dspy.OutputField(desc="The answer")
    }
    
    Sig = dspy.make_signature(
        fields_simple,
        instructions="Answer the question.",
        signature_name="TestSigDynamic"
    )
    
    assert Sig.instructions == "Answer the question."
    assert "question" in Sig.input_fields
    assert "answer" in Sig.output_fields
