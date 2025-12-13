import pytest
from app.engine.router import make_router
from app.engine.state import GraphState
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import END

# Helper to create state
def create_state(content: str) -> GraphState:
    return {"messages": [HumanMessage(content=content)]}

class TestRouterNode:
    
    def test_router_contains(self):
        routes = [{"condition": "contains", "value": "please", "target_handle": "route-1"}]
        handle_map = {"route-1": "node_a", "default": "node_b"}
        
        router = make_router(routes, handle_map, "node_b")
        
        # Match
        assert router(create_state("Yes, please do it")) == "node_a"
        # No Match
        assert router(create_state("No, thank you")) == "node_b"

    def test_router_equals(self):
        routes = [{"condition": "equals", "value": "STOP", "target_handle": "route-stop"}]
        handle_map = {"route-stop": "end_node", "default": "continue_node"}
        
        router = make_router(routes, handle_map, "continue_node")
        
        # Match Case Insensitive
        assert router(create_state("stop")) == "end_node"
        assert router(create_state("STOP")) == "end_node"
        # Partial match should fail
        assert router(create_state("stop it")) == "continue_node"

    def test_router_starts_with(self):
        routes = [{"condition": "starts_with", "value": "/cmd", "target_handle": "cmd_node"}]
        handle_map = {"cmd_node": "executor"}
        
        router = make_router(routes, handle_map, END)
        
        assert router(create_state("/cmd run")) == "executor"
        assert router(create_state("Hello /cmd")) == END

    def test_router_regex(self):
        # Match email-like pattern
        routes = [{"condition": "regex", "value": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "target_handle": "email-node"}]
        handle_map = {"email-node": "processor"}
        
        router = make_router(routes, handle_map, END)
        
        assert router(create_state("Contact me at test@example.com please")) == "processor"
        assert router(create_state("No email here")) == END

    def test_router_multiple_routes(self):
        routes = [
            {"condition": "contains", "value": "urgent", "target_handle": "priority"},
            {"condition": "contains", "value": "help", "target_handle": "support"}
        ]
        handle_map = {"priority": "A", "support": "B"}
        
        router = make_router(routes, handle_map, "C")
        
        # First match wins (order matters in list)
        assert router(create_state("This is urgent help needed")) == "A"
        assert router(create_state("I need help")) == "B"
        assert router(create_state("Just chatting")) == "C"

if __name__ == "__main__":
    pytest.main([__file__])
