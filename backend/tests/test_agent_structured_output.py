import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.nodes.agent import GenericAgentNode
from langchain_core.messages import AIMessage, HumanMessage

@pytest.mark.asyncio
async def test_agent_structured_output_parsing():
    # Mock LLM response
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = AIMessage(content='{"sentiment": "positive", "score": 95}')
    mock_llm.bind_tools.return_value = mock_llm

    # Mock Factory
    with patch("app.nodes.agent.get_llm_profile", return_value=MagicMock(id="test-profile")), \
         patch("app.nodes.agent.create_llm_instance", return_value=mock_llm):

        # Config with Output Schema
        config = {
            "profile_id": "test",
            "output_schema": [
                {"name": "sentiment", "type": "string", "description": "The sentiment"},
                {"name": "score", "type": "number", "description": "The score"}
            ]
        }
        
        node = GenericAgentNode("agent-1", config)
        
        # Initial State
        state = {
            "messages": [HumanMessage(content="Hello")],
            "context": {}
        }
        
        # Run
        result = await node(state)
        
        # Verify Context Update
        assert "context" in result
        assert result["context"] == {"sentiment": "positive", "score": 95}
        
        # Verify Messages
        assert len(result["messages"]) == 1
        assert result["messages"][0].content == '{"sentiment": "positive", "score": 95}'
        
        # Verify System Prompt Injection
        # We can inspect the calls to output valid system prompt
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert "IMPORTANT: You must output a valid JSON object matching this schema" in call_args[0].content
        assert '"sentiment": "string - The sentiment"' in call_args[0].content
