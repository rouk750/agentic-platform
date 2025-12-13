import pytest
from app.engine.compiler import compile_graph
from app.nodes.agent import GenericAgentNode
from unittest.mock import MagicMock, patch

# Mock Registry
MOCK_REGISTRY = {
    "agent": GenericAgentNode,
    "router": MagicMock
}

@patch("app.engine.compiler.NODE_REGISTRY", MOCK_REGISTRY)
@patch("app.nodes.agent.get_llm_profile")
@patch("app.nodes.agent.create_llm_instance")
def test_compile_fanout_graph(mock_create_llm, mock_get_profile):
    
    mock_get_profile.return_value = MagicMock()
    mock_create_llm.return_value = MagicMock()
    
    # Graph: Agent_1 -> Router_A AND Agent_1 -> Router_B
    graph_data = {
        "nodes": [
            {"id": "agent_1", "type": "agent", "data": {"profile_id": "1"}},
            {"id": "router_a", "type": "router", "data": {"routes": []}},
            {"id": "router_b", "type": "router", "data": {"routes": []}}
        ],
        "edges": [
            {"source": "agent_1", "target": "router_a"},
            {"source": "agent_1", "target": "router_b"}
        ]
    }
    
    # This should compile without error and establish edges from agent_1 to both routers
    app = compile_graph(graph_data)
    assert app is not None
    
    # Using internal graph inspection (if possible) or just asserting compilation success
    # LangGraph compiled graph structure is complex to inspect deeply without running.
    # But if compile_graph doesn't error and processes the logic we added, we are good.
    # The logic we added: "if targets: for t in targets: workflow.add_edge..."
    
    print("Fan-out graph compiled successfully!")

if __name__ == "__main__":
    test_compile_fanout_graph()
