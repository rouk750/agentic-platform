
import pytest
from app.nodes.iterator_node import IteratorNode

def test_iterator_init_and_processing():
    """Verify Iterator Node logic handles queue initialization and processing correctly."""
    
    node_id = "iter_1"
    config = {
        "input_list_variable": "my_list",
        "output_item_variable": "current_item"
    }
    node = IteratorNode(node_id, config)
    
    # CASE 1: Initialization (First Run)
    initial_state = {
        "messages": [],
        "context": {
            "my_list": ["item1", "item2"]
        }
    }
    
    result = node.invoke(initial_state)
    
    # Check Signal
    assert result["_signal"] == "NEXT"
    assert result["last_sender"] == node_id
    
    # Check Output Variable (in context)
    assert "context" in result
    assert result["context"]["current_item"] == "item1"
    
    # Check Queue State
    # NOTE: The node returns a DICT update. It doesn't modify the input state reference in place usually, 
    # but LangGraph merges it. For this Unit Test, we check the RETURN value.
    # The return value key for queue is f"_iterator_queue_{node_id}"
    queue_key = f"_iterator_queue_{node_id}"
    assert queue_key in result["context"]
    assert result["context"][queue_key] == ["item2"] # One popped
    
    # Check Progress Metadata
    meta = result["_iterator_metadata"]
    assert meta["node_id"] == node_id
    assert meta["current"] == 1
    assert meta["total"] == 2

    # CASE 2: Next Iteration
    # We simulate the state merging that LangGraph would do
    state_step_2 = {
        "messages": [],
        "context": {
            "my_list": ["item1", "item2"],
            queue_key: result["context"][queue_key], # ["item2"]
            f"_iterator_total_{node_id}": 2
        }
    }
    
    result_2 = node.invoke(state_step_2)
    assert result_2["_signal"] == "NEXT"
    assert result_2["context"]["current_item"] == "item2"
    assert result_2["context"][queue_key] == [] # All popped
    
    meta_2 = result_2["_iterator_metadata"]
    assert meta_2["current"] == 2
    
    # CASE 3: Completion
    state_step_3 = {
        "messages": [],
        "context": {
            "my_list": ["item1", "item2"],
            queue_key: result_2["context"][queue_key], # []
            f"_iterator_total_{node_id}": 2
        }
    }
    
    result_3 = node.invoke(state_step_3)
    assert result_3["_signal"] == "COMPLETE"
    assert result_3["context"]["current_item"] is None # Or cleared
    
    meta_3 = result_3["_iterator_metadata"]
    assert meta_3["progress"] == "Done"

def test_iterator_handles_invalid_input():
    """Verify handling of missing or non-list inputs."""
    node = IteratorNode("iter_err", {})
    state = {"context": {"items": "not-a-list"}}
    
    result = node.invoke(state)
    # Should treat as empty list and finish immediately
    assert result["_signal"] == "COMPLETE"
    assert result["_iterator_metadata"]["total"] == 0
