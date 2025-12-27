
import pytest
import shutil
import os
from unittest.mock import MagicMock, patch
from app.services.rag_service import RagService, ChromaNodeConfig, ChromaMode

# Temp DB Path
TEST_DB_PATH = "./test_chroma_db"

@pytest.fixture
def rag_service():
    return RagService()

@pytest.fixture
def clean_db(request):
    # Unique path per test to avoid locks
    path = f"{TEST_DB_PATH}_{request.node.name}"
    if os.path.exists(path):
        shutil.rmtree(path)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)

@pytest.fixture
def chroma_config(clean_db):
    return ChromaNodeConfig(
        mode=ChromaMode.LOCAL,
        path=clean_db, # Use the unique path yielded by clean_db
        collection_name="test_collection"
    )

@pytest.mark.asyncio
async def test_ingest_text_simple(rag_service, chroma_config, clean_db):
    text = "Agentic Platform is a cool project. It uses DSPy."
    
    # Mock LLM extraction to avoid API call
    with patch("app.services.rag_service.get_dspy_lm") as mock_get_lm:
        # We don't need real extraction for this test, just ensure it runs
        res = rag_service.ingest_text(text, chroma_config, llm_profile=None)
        
        assert res["status"] == "success"
        assert res["chunks"] > 0

@pytest.mark.asyncio
async def test_search_simple(rag_service, chroma_config, clean_db):
    # Ingest first
    text = "The secret code is 12345."
    rag_service.ingest_text(text, chroma_config)
    
    # Search
    # Mock embedding function inside search if needed, but we used default fallback in service
    # If no OpenAI key, it might use sentence-transformers if installed or fail.
    # We should mock _get_embedding_function if we want deterministic unit test without ext deps.
    
    with patch.object(rag_service, "_get_embedding_function", side_effect=ImportError("No embedding lib")):
        # If we force error, it falls back to native client search which works with default embeddings
        # BUT wait, native client defaults also need libraries (onnxruntime + tokenizers).
        # Assuming dev environment has them (chromadb installs them).
        
        # Actually, let's just let it run. If it fails due to missing lib, we'll know.
        pass
        
    query = "What is the secret code?"
    context = rag_service.search(query, chroma_config)
    
    assert "12345" in context

