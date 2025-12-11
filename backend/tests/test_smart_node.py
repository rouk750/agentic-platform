import pytest
from unittest.mock import MagicMock, patch, mock_open
from app.nodes.smart_node import SmartNode
from app.models.settings import LLMProfile

@pytest.fixture
def mock_dspy():
    with patch('app.nodes.smart_node.dspy') as mock:
        yield mock

@pytest.fixture
def mock_get_dspy_lm():
    with patch('app.nodes.smart_node.get_dspy_lm') as mock:
        mock.return_value = MagicMock()
        yield mock

@pytest.mark.asyncio
async def test_smart_node_signature_creation(mock_dspy, mock_get_dspy_lm):
    # Setup
    node_data = {
        "label": "Test Node",
        "mode": "ChainOfThought",
        "inputs": [{"name": "question", "desc": "Question"}],
        "outputs": [{"name": "answer", "desc": "Answer"}],
        "goal": "Answer the question.",
        "llm_profile": {"id": 1, "name": "GPT-4", "provider": "openai", "model_id": "gpt-4"}
    }
    node = SmartNode("node_1", node_data)
    
    # Mock context manager
    mock_dspy.context.return_value.__enter__.return_value = None

    # Execute
    state = {"question": "What is 2+2?"}
    await node.invoke(state)

    # Verify make_signature called correctly
    mock_dspy.make_signature.assert_called()
    call_args = mock_dspy.make_signature.call_args
    assert call_args.kwargs['signature_name'] == "Node_node_1"
    assert call_args.kwargs['instructions'] == "Answer the question."
    assert "question" in call_args.kwargs['input_fields']
    assert "answer" in call_args.kwargs['output_fields']

@pytest.mark.asyncio
async def test_smart_node_loads_compiled_json(mock_dspy, mock_get_dspy_lm):
    # Setup
    node_data = {
        "label": "Compiled Node",
        "mode": "Predict",
        "inputs": [{"name": "x"}],
        "outputs": [{"name": "y"}],
        "llm_profile": {"id": 1, "model_id": "gpt-3.5"}
    }
    node = SmartNode("node_compiled", node_data)
    
    # Mock module
    mock_module = MagicMock()
    mock_dspy.Predict.return_value = mock_module

    # Mock file existence and loading
    with patch('os.path.exists', return_value=True):
        await node.invoke({"x": "test"})
    
    # Verify load called
    mock_module.load.assert_called_with("resources/smart_nodes/node_compiled_compiled.json")

