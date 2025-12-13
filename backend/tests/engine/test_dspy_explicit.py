
import dspy
import pytest
import asyncio
from app.nodes.smart_node import SmartNode
from app.models.settings import LLMProfile

# Mock LM that fails at first then succeeds to test retry logic
class MockFaultyLM(dspy.LM):
    def __init__(self):
        super().__init__("mock")
        self.attempts = 0

    def basic_request(self, prompt, **kwargs):
        self.attempts += 1
        print(f"\n[MockLM] Call #{self.attempts}")
        
        # Scenario: User asks for JSON
        if self.attempts == 1:
            return ["I cannot generate json"] 
            
        return ['```json\n{"json_output": "valid json now"}\n```']

    def __call__(self, prompt=None, **kwargs):
        return self.basic_request(prompt, **kwargs)

@pytest.mark.asyncio
async def test_smart_node_explicit_guardrail():
    print("=== Testing Smart Node Refine (Explicit Flag) ===")
    
    # 1. Setup Mock LM
    mock_lm = MockFaultyLM()
    # 1. Setup Mock LM
    mock_lm = MockFaultyLM()
    # dspy.settings.configure(lm=mock_lm) - REMOVED to avoid async task conflicts
    
    # 2. Configure Smart Node with explicit 'force_json' flag
    node_data = {
        "label": "JSON Generator",
        "llm_profile": {"id": 1, "name": "test", "provider": "openai", "model_id": "gpt-4-mock", "api_key": "mock"},
        "inputs": [{"name": "topic", "desc": "Topic"}],
        
        # HERE IS THE CHANGE: Explicit flag
        "outputs": [{"name": "json_output", "desc": "Result", "force_json": True}],
        
        "goal": "Generate a JSON object.",
        "mode": "Predict"
    }
    
    node = SmartNode("node_explicit_1", node_data)
    
    # Inject our mock LM directly via monkeypatch
    import app.nodes.smart_node as sn_module
    original_get_lm = sn_module.get_dspy_lm
    sn_module.get_dspy_lm = lambda p: mock_lm
    
    try:
        # 3. Invoke
        print("Invoking SmartNode...")
        result = await node.invoke({"topic": "test"})
        
        print("\n=== Result ===")
        print(result)
        
        if "messages" in result and "valid json now" in str(result):
             print("\n✅ SUCCESS: SmartNode recovered using EXPLICIT guardrail!")
        else:
             print("\n❌ FAILURE: Did not get expected corrected JSON.")
             
    finally:
        # Restore
        sn_module.get_dspy_lm = original_get_lm

if __name__ == "__main__":
    asyncio.run(test_smart_node_explicit_guardrail())
