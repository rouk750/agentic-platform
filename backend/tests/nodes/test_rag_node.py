
import pytest
from unittest.mock import MagicMock, patch
from app.nodes.rag_node import RAGNode
from app.schemas.chroma_config import ChromaNodeConfig
from langchain_core.messages import HumanMessage, SystemMessage

def test_rag_node_init():
    node_id = "rag_1"
    config = {
        "chroma": {"mode": "local", "collection_name": "test_node"},
        "action": "write"
    }
    node = RAGNode(node_id, config)
    assert node.action == "write"
    assert node.chroma_config.mode == "local"
    assert node.chroma_config.collection_name == "test_node"

@pytest.mark.asyncio
async def test_rag_node_read_fallback():
    # Test fallback to last message
    node = RAGNode("rag_1", {"action": "read"})
    
    # Mock service
    node.service.search = MagicMock(return_value="Mocked Context")
    
    state = {
        "messages": [HumanMessage(content="Hello World")]
    }
    
    result = node(state)
    
    node.service.search.assert_called_once()
    assert "rag_context" in result
    assert result["rag_context"] == "Mocked Context"
    assert isinstance(result["messages"][0], SystemMessage)

def test_rag_node_write_explicit():
    node = RAGNode("rag_1", {"action": "write"})
    node.service.ingest_text = MagicMock(return_value={"status": "ok", "chunks": 1})
    
    state = {
        "content": "Some content to ingest"
    }
    
    result = node(state)
    
    # Check that ingest_text was called with correct arguments
    # Signature: ingest_text(text, chroma_config, llm_profile=None, dedup_config=None)
    assert node.service.ingest_text.called
    call_args = node.service.ingest_text.call_args
    assert call_args[0][0] == "Some content to ingest"  # text argument
    assert call_args[0][1] == node.chroma_config  # chroma_config argument
    # dedup_config is passed as keyword argument
    assert "dedup_config" in call_args[1]
    
    assert result["rag_write_status"]["status"] == "ok"
