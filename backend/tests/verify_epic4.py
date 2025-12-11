import asyncio
import pytest
from unittest.mock import MagicMock, patch

from app.engine.compiler import compile_graph
from app.engine.state import GraphState
from langchain_core.messages import HumanMessage, AIMessage

# Mock data
MOCK_GRAPH_JSON = {
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
            "source": "start_node", # Placeholder for start
            "target": "agent_1",
            "sourceHandle": None
        },
        {
            "source": "agent_1",
            "target": "END"
        }
    ]
}

# Mock LLM
class MockLLM:
    async def ainvoke(self, messages):
        return AIMessage(content="Hello from Mock LLM!")

@pytest.mark.asyncio
async def test_compile_and_run():
    print("Starting verification test...")
    
    # 1. Patch get_llm_profile and create_llm_instance
    with patch("app.nodes.agent.get_llm_profile") as mock_get_profile, \
         patch("app.nodes.agent.create_llm_instance") as mock_create_llm:
         
        mock_get_profile.return_value = MagicMock(provider="openai", model_id="gpt-4", temperature=0.7)
        mock_create_llm.return_value = MockLLM()
        
        # 2. Compile Graph
        print("Compiling graph...")
        # Note: compile_graph expects "data" structure roughly matching React Flow
        # Our mock JSON is simplified.
        # compiler.py expects:
        # nodes list with {id, type, data}
        # edges list with {source, target, sourceHandle}
        # And it handles "START" connection.
        
        # We need to make sure 'start_node' logic in compiler works or we just provide a node that has no incoming edges.
        # In our mock edges, 'start_node' -> 'agent_1'. 
        # But 'start_node' is NOT in the nodes list. 
        # The compiler.py logic:
        # "If source_id not in node_ids: continue" -> So the edge 'start_node' -> 'agent_1' would be ignored!
        # And "orphans = ... agent_1" (if agent_1 has no incoming valid edges).
        # So agent_1 will be connected to START.
        
        app = compile_graph(MOCK_GRAPH_JSON)
        assert app is not None
        print("Graph compiled successfully.")
        
        # 3. Execute
        print("Executing graph...")
        inputs = {"messages": [HumanMessage(content="Hi")]}
        config = {"configurable": {"thread_id": "test_thread"}}
        
        # We need to use ainvoke or stream
        result = await app.ainvoke(inputs, config=config)
        
        # 4. Verify Output
        print("Result:", result)
        messages = result["messages"]
        assert len(messages) == 2 # Human + AI
        assert messages[1].content == "Hello from Mock LLM!"
        assert result["last_sender"] == "agent_1"
        
        print("Verification passed!")

if __name__ == "__main__":
    # Manually run async test if not using pytest runner
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_compile_and_run())
