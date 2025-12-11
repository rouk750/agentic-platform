from typing import Any, Dict
from langchain_core.messages import SystemMessage
from app.engine.state import GraphState

class RAGNode:
    def __init__(self, node_id: str, config: dict = None):
        self.node_id = node_id
        self.config = config or {}
        self.collection_name = self.config.get('collection', 'default')
        
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """
        Retrieves context and adds it as a SystemMessage.
        Mock implementation for now.
        """
        # In a real implementation, we would:
        # 1. Get the query (last user message)
        # 2. Embed it
        # 3. Search vector DB (Chroma/Neo4j)
        # 4. Return top K docs
        
        mock_docs = [
            f"Context from collection '{self.collection_name}': Data point A",
            f"Context from collection '{self.collection_name}': Data point B"
        ]
        
        context_str = "\n".join(mock_docs)
        
        system_content = f"Background Context:\n{context_str}"
        
        return {
            "messages": [SystemMessage(content=system_content)],
            "last_sender": self.node_id
        }
