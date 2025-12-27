"""
RAG Tools for dynamic read/write operations.
These tools are created dynamically based on RAG Node configuration.
"""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
from app.services.rag_service import RagService
from app.schemas.chroma_config import ChromaNodeConfig


class RagSearchInput(BaseModel):
    """Input schema for RAG search operation."""
    query: str = Field(description="The search query to find relevant context in the knowledge base")


class RagIngestInput(BaseModel):
    """Input schema for RAG ingest operation."""
    content: str = Field(description="The content to store in the knowledge base. Can be text, facts, or any information you want to remember.")


def create_rag_search_tool(
    collection_name: str,
    chroma_config: ChromaNodeConfig,
    default_k: int = 5
) -> StructuredTool:
    """
    Create a RAG search tool for a specific collection.
    
    Args:
        collection_name: Name of the ChromaDB collection
        chroma_config: ChromaDB configuration
        default_k: Default number of results to retrieve
        
    Returns:
        StructuredTool for searching the RAG collection
    """
    service = RagService()
    
    def search_rag(query: str) -> str:
        """Search for relevant context in the knowledge base."""
        try:
            context = service.search(query, chroma_config, k=default_k)
            if not context or context.strip() == "":
                return f"No relevant information found in '{collection_name}' knowledge base for query: {query}"
            return context
        except Exception as e:
            return f"Error searching '{collection_name}' knowledge base: {str(e)}"
    
    return StructuredTool.from_function(
        func=search_rag,
        name=f"rag_search_{collection_name}",
        description=f"Search for relevant information in the '{collection_name}' knowledge base. Use this when you need context, facts, or information about a specific topic. Returns the most relevant text chunks.",
        args_schema=RagSearchInput
    )


def create_rag_ingest_tool(
    collection_name: str,
    chroma_config: ChromaNodeConfig,
    dedup_config: dict = None
) -> StructuredTool:
    """
    Create a RAG ingest tool for a specific collection.
    
    Args:
        collection_name: Name of the ChromaDB collection
        chroma_config: ChromaDB configuration
        dedup_config: Deduplication configuration
        
    Returns:
        StructuredTool for ingesting content into the RAG collection
    """
    service = RagService()
    dedup_config = dedup_config or {"enabled": True, "threshold": 0.95}
    
    def ingest_rag(content: str) -> str:
        """Store new information in the knowledge base."""
        try:
            result = service.ingest_text(content, chroma_config, dedup_config=dedup_config)
            status = result.get("status", "unknown")
            chunks = result.get("chunks", 0)
            skipped = result.get("skipped_chunks", 0)
            
            if status == "success":
                msg = f"Successfully stored {chunks} chunk(s) in '{collection_name}' knowledge base."
                if skipped > 0:
                    msg += f" {skipped} duplicate(s) skipped."
                return msg
            else:
                return f"Ingestion completed with status: {status}"
        except Exception as e:
            return f"Error storing in '{collection_name}' knowledge base: {str(e)}"
    
    return StructuredTool.from_function(
        func=ingest_rag,
        name=f"rag_ingest_{collection_name}",
        description=f"Store new information in the '{collection_name}' knowledge base. Use this when you need to remember or save important information, facts, or context for later retrieval. The information will be chunked and indexed automatically.",
        args_schema=RagIngestInput
    )
