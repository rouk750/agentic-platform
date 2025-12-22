"""
Generic tests for Compiler
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from app.engine.compiler import compile_graph
from langgraph.graph import StateGraph

@pytest.fixture
def mock_nodes():
    with patch("app.engine.compiler.GenericAgentNode") as MockAgent, \
         patch("app.engine.compiler.ToolNode") as MockTool, \
         patch("app.engine.compiler.IteratorNode") as MockIterator:
        yield MockAgent, MockTool, MockIterator

def test_compile_empty_graph():
    """Test compiling an empty graph structure."""
    graph_data = {"nodes": [], "edges": []}
    
    with patch("app.engine.compiler.StateGraph") as MockStateGraph:
        # Mock the graph instance to avoid errors during compilation
        mock_workflow = MockStateGraph.return_value
        mock_workflow.compile.return_value = MagicMock()
        
        workflow = compile_graph(graph_data)
        assert workflow is not None

def test_compile_graph_with_nodes_and_edges(mock_nodes):
    """Test compiling a simple graph."""
    graph_data = {
        "nodes": [
            {"id": "1", "type": "agent", "data": {}},
            {"id": "2", "type": "tool", "data": {}}
        ],
        "edges": [
            {"source": "1", "target": "2"}
        ]
    }
    
    with patch("app.engine.compiler.StateGraph") as MockStateGraph:
        mock_workflow = MockStateGraph.return_value
        mock_workflow.compile.return_value = MagicMock()
        
        compile_graph(graph_data)
        
        # Verify nodes were added
        assert mock_workflow.add_node.call_count == 2
        
        # Verify edge added (plus potentially START edge if orphans detected)
        # compile_graph logic adds START -> 1 (orphan)
        # and 1 -> 2
        # So at least 2 add_edge calls
        assert mock_workflow.add_edge.call_count >= 1

def test_entry_point_detection(mock_nodes):
    """Test start node detection."""
    graph_data = {
        "nodes": [
            {"id": "node_start", "type": "agent", "data": {"isStart": True}},
            {"id": "other", "type": "agent", "data": {}}
        ],
        "edges": []
    }
    
    with patch("app.engine.compiler.StateGraph") as MockStateGraph:
        mock_workflow = MockStateGraph.return_value
        mock_workflow.compile.return_value = MagicMock()
        
        from langgraph.graph import START
        compile_graph(graph_data)
        
        # Logic uses add_edge(START, id)
        mock_workflow.add_edge.assert_any_call(START, "node_start")

def test_hitl_detection(mock_nodes):
    """Test Human-in-the-Loop interrupt setup."""
    graph_data = {
        "nodes": [
            {"id": "1", "type": "agent", "data": {"require_approval": True}}
        ],
        "edges": []
    }
    
    with patch("app.engine.compiler.StateGraph") as MockStateGraph:
        mock_workflow = MockStateGraph.return_value
        mock_workflow.compile.return_value = MagicMock()
        
        compile_graph(graph_data)
        
        # Verify compile called with interrupt_before
        args, kwargs = mock_workflow.compile.call_args
        assert "interrupt_before" in kwargs
        assert "1" in kwargs["interrupt_before"]
