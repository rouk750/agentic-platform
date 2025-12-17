
import pytest
from unittest.mock import MagicMock, patch
from app.engine.compiler import compile_graph

def test_compiler_collects_interrupt_nodes():
    """Verify that nodes with 'require_approval' are added to interrupt_before."""
    
    graph_data = {
        "nodes": [
            {
                "id": "start_node",
                "type": "agent",
                "data": {"label": "Start", "isStart": True}
            },
            {
                "id": "hitl_node",
                "type": "agent",
                "data": {
                    "label": "Approver",
                    "require_approval": True
                }
            },
            {
                "id": "normal_node",
                "type": "agent",
                "data": {"label": "Worker"}
            }
        ],
        "edges": [
            {"source": "start_node", "target": "hitl_node"},
            {"source": "hitl_node", "target": "normal_node"},
        ]
    }
    
    # We need to patch workflow.compile to verify call args because CompiledGraph introspection varies
    with patch("langgraph.graph.StateGraph.compile") as mock_compile:
        # Mock the return value to be a dummy object so compile_graph doesn't crash on return
        mock_compile.return_value = MagicMock()
        
        compile_graph(graph_data)
        
        # Verify interrupt_before argument
        call_args = mock_compile.call_args
        assert call_args is not None
        
        # kwargs are in call_args[1]
        kwargs = call_args[1]
        assert "interrupt_before" in kwargs
        interrupts = kwargs["interrupt_before"]
        
        assert "hitl_node" in interrupts
        assert "start_node" not in interrupts
        assert "normal_node" not in interrupts
