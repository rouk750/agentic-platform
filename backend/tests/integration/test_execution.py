import pytest
import asyncio
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.engine.compiler import compile_graph
from app.nodes.agent import GenericAgentNode
# Note: GraphState is a TypedDict, so we just use dict in tests usually or import if needed

# --- Mocks ---

class MockLLM:
    async def ainvoke(self, messages):
        return AIMessage(content="Hello from Mock LLM!")

# --- Tests ---

@pytest.mark.asyncio
async def test_compile_and_run_simple_graph():
    """Verify full cycle: JSON Graph -> Compile -> Execute (Mock LLM)."""
    
    mock_graph_json = {
        "nodes": [
            {
                "id": "agent_1",
                "type": "agent",
                "data": {
                    "profile_id": 1,
                    "system_prompt": "You are a helpful assistant."
                }
            }
        ],
        "edges": [
            {
                "source": "start_node",
                "target": "agent_1",
                "sourceHandle": None
            },
            {
                "source": "agent_1",
                "target": "END"
            }
        ]
    }

    with patch("app.nodes.agent.get_llm_profile") as mock_get_profile, \
         patch("app.nodes.agent.create_llm_instance") as mock_create_llm:
         
        mock_get_profile.return_value = MagicMock(provider="openai", model_id="gpt-4", temperature=0.7)
        mock_create_llm.return_value = MockLLM()
        
        # Compile
        app = compile_graph(mock_graph_json)
        assert app is not None
        
        # Execute
        inputs = {"messages": [HumanMessage(content="Hi")]}
        config = {"configurable": {"thread_id": "test_thread_1"}}
        
        result = await app.ainvoke(inputs, config=config)
        
        # Verify
        messages = result["messages"]
        assert len(messages) == 2 
        # Agent response is wrapped with sender header
        assert "Hello from Mock LLM!" in messages[1].content
        assert result["last_sender"] == "agent_1"

@pytest.mark.asyncio
async def test_agent_loop_limit():
    """Verify that GenericAgentNode enforces max_iterations."""
    
    node_id = "agent_TEST"
    max_iters = 2
    
    # Init Node
    config = {
        "profile_id": "mock_profile",
        "max_iterations": max_iters
    }
    agent = GenericAgentNode(node_id, config)
    
    # State with messages already equal to limit
    messages_at_limit = [
        HumanMessage(content="Start"),
        AIMessage(content="Rep 1", name=node_id),
        HumanMessage(content="User reply"),
        AIMessage(content="Rep 2", name=node_id)
    ]
    
    state = {
        "messages": messages_at_limit,
        "context": {},
        "last_sender": None
    }
    
    # Expect error
    with pytest.raises(ValueError, match="reached max iterations limit"):
        await agent(state)
