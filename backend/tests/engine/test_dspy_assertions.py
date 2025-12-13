
import dspy
import pytest
import asyncio
from app.nodes.smart_node import SmartNode
from app.models.settings import LLMProfile, ProviderType

# Mock LM that fails at first then succeeds to test retry logic
class MockFaultyLM(dspy.LM):
    def __init__(self):
        super().__init__("mock")
        self.attempts = 0

    def basic_request(self, prompt, **kwargs):
        self.attempts += 1
        print(f"\n[MockLM] Call #{self.attempts}")
        
        # Scenario: User asks for JSON
        # Attempt 1: Returns invalid markdown or bad json
        if self.attempts == 1:
            return ["Here is the json: { key: 'invalid' }"] # Missing quotes keys
            
        # Attempt 2: Returns valid JSON (after assertion feedback)
        return ['```json\n{"json_output": "valid json now"}\n```']

    def __call__(self, prompt=None, **kwargs):
        return self.basic_request(prompt, **kwargs)

@pytest.mark.asyncio
async def test_smart_node_assertion():
    print("=== Testing Smart Node JSON Assertion ===")
    
    # 1. Setup Mock LM to be used globally or injected
    mock_lm = MockFaultyLM()
    # 1. Setup Mock LM to be used globally or injected
    mock_lm = MockFaultyLM()
    # dspy.settings.configure(lm=mock_lm) - REMOVED to avoid async task conflicts
    
    # 2. Configure Smart Node
    # Output name "json_output" should trigger auto-assertion
    node_data = {
        "label": "JSON Generator",
        "llm_profile": {"id": 1, "name": "test", "provider": "openai", "model_id": "gpt-4-mock", "api_key": "mock"},
        "inputs": [{"name": "topic", "desc": "Topic"}],
        "outputs": [{"name": "json_output", "desc": "Result in JSON"}],
        "goal": "Generate a JSON object.",
        "mode": "Predict"
    }
    
    node = SmartNode("node_1", node_data)
    
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
             print("\n✅ SUCCESS: SmartNode recovered from invalid JSON!")
        else:
             print("\n❌ FAILURE: Did not get expected corrected JSON.")
             
    finally:
        # Restore
        sn_module.get_dspy_lm = original_get_lm

if __name__ == "__main__":
    asyncio.run(test_smart_node_assertion())
