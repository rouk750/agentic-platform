import pytest
from app.engine.compiler import compile_graph
from app.nodes.agent import GenericAgentNode
from unittest.mock import MagicMock, patch

# Mock the registry to avoid needing real node classes or LLMs
MOCK_REGISTRY = {
    "agent": GenericAgentNode,
    "tool_node": MagicMock
}

@patch("app.engine.compiler.NODE_REGISTRY", MOCK_REGISTRY)
@patch("app.nodes.agent.get_llm_profile")
@patch("app.nodes.agent.create_llm_instance")
def test_compile_cyclic_graph(mock_create_llm, mock_get_profile):
    
    # Mock LLM setup
    mock_get_profile.return_value = MagicMock()
    mock_create_llm.return_value = MagicMock()
    
    # A graph with a cycle: Agent -> Tool -> Agent
    # All nodes have incoming edges, so "orphans" logic fails.
    graph_data = {
        "nodes": [
            {"id": "agent_1", "type": "agent", "data": {"profile_id": "1"}},
            {"id": "tool_1", "type": "tool_node", "data": {}}
        ],
        "edges": [
            {"source": "agent_1", "target": "tool_1"},
            {"source": "tool_1", "target": "agent_1"}
        ]
    }
    
    # This should NOT match "START" edge explicitly.
    # It should trigger the fallback logic to find "agent_1".
    
    app = compile_graph(graph_data)
    assert app is not None
    print("Cyclic graph compiled successfully!")

if __name__ == "__main__":
    test_compile_cyclic_graph()
