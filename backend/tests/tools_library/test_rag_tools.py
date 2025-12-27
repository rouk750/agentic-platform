"""
Tests for RAG Tools functionality
"""

import pytest
from app.tools_library.rag_tools import create_rag_search_tool, create_rag_ingest_tool
from app.schemas.chroma_config import ChromaNodeConfig
from unittest.mock import MagicMock


def test_create_rag_search_tool():
    """Test RAG search tool creation."""
    config = ChromaNodeConfig(
        collection_name="test_collection",
        mode="local",
        path="./test_db"
    )
    
    tool = create_rag_search_tool("test_collection", config, default_k=5)
    
    assert tool.name == "rag_search_test_collection"
    assert "search" in tool.description.lower()
    assert "test_collection" in tool.description


def test_create_rag_ingest_tool():
    """Test RAG ingest tool creation."""
    config = ChromaNodeConfig(
        collection_name="test_collection",
        mode="local",
        path="./test_db"
    )
    
    tool = create_rag_ingest_tool("test_collection", config)
    
    assert tool.name == "rag_ingest_test_collection"
    assert "store" in tool.description.lower() or "ingest" in tool.description.lower()
    assert "test_collection" in tool.description


def test_rag_node_get_tools():
    """Test that RAG node exposes correct tools based on capabilities."""
    from app.nodes.rag_node import RAGNode
    
    # Test with both capabilities
    config = {
        "capabilities": ["read", "write"],
        "chroma": {"collection_name": "docs", "mode": "local"},
        "k": 10
    }
    node = RAGNode("rag_1", config)
    tools = node.get_tools()
    
    assert len(tools) == 2
    tool_names = [t.name for t in tools]
    assert "rag_search_docs" in tool_names
    assert "rag_ingest_docs" in tool_names


def test_rag_node_get_tools_read_only():
    """Test RAG node with read capability only."""
    from app.nodes.rag_node import RAGNode
    
    config = {
        "capabilities": ["read"],
        "chroma": {"collection_name": "docs", "mode": "local"}
    }
    node = RAGNode("rag_1", config)
    tools = node.get_tools()
    
    assert len(tools) == 1
    assert tools[0].name == "rag_search_docs"


def test_rag_node_backward_compatibility():
    """Test that old action format is migrated to capabilities."""
    from app.nodes.rag_node import RAGNode
    
    # Old format with action='read'
    config = {
        "action": "read",
        "chroma": {"collection_name": "docs", "mode": "local"}
    }
    node = RAGNode("rag_1", config)
    
    assert node.capabilities == ["read"]
    tools = node.get_tools()
    assert len(tools) == 1
    assert tools[0].name == "rag_search_docs"
