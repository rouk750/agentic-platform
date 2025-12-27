
import logging
from typing import List, Dict, Any, Optional
import dspy
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.schemas.chroma_config import ChromaNodeConfig, ChromaMode
from app.models.settings import LLMProfile
from app.engine.dspy_utils import get_dspy_lm
from app.services.llm_factory import get_first_profile

logger = logging.getLogger(__name__)

# --- DSPy Signatures ---

class ExtractEntities(dspy.Signature):
    """Extract key named entities (Person, Organization, Location, Project, Technology) from the text to be used as metadata."""
    text = dspy.InputField(desc="The content to analyze")
    entities = dspy.OutputField(desc="A list of comma-separated entities found in the text. e.g. 'Project Alpha, John Doe, New York'")

class ExtractQueryEntities(dspy.Signature):
    """Extract key entities from a search query to filter results."""
    query = dspy.InputField(desc="The user search query")
    entities = dspy.OutputField(desc="A list of comma-separated entities found in the query. e.g. 'React, Vite'. Return empty string if none.")

# --- Service ---

class RagService:
    def __init__(self):
        self._clients = {} # Cache clients if needed, or just recreate (lightweight)

    def _get_client(self, config: ChromaNodeConfig) -> chromadb.ClientAPI:
        """Get or create a Chroma Client based on config."""
        # TODO: Caching strategy based on path/host+port
        if config.mode == ChromaMode.SERVER:
            return chromadb.HttpClient(host=config.host, port=config.port)
        else:
            return chromadb.PersistentClient(path=config.path)

    def _get_embedding_function(self):
        """
        Return the embedding function. 
        For now, we rely on Chroma's default (all-MiniLM-L6-v2) if we pass None to the add/query methods of native client.
        However, LangChain abstraction requires one.
        
        We will use a specialized wrapper or 'sentence-transformers' if available. 
        Given we didn't add sentence-transformers explicitly (it might be in chromadb dep), 
        we'll try to use a simple fallback or 'langchain_community.embeddings.sentence_transformer' if implied.
        
        Actually, 'chromadb.utils.embedding_functions' has 'DefaultEmbeddingFunction'.
        """
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        # This is compatible with Chroma native, but LangChain demands a LangChain Embeddings class.
        # We will wrap it or use a Generic one.
        
        # Simpler approach: Use OpenAI embeddings if available, else standard.
        # For this implementation, let's use a "passthrough" or assume OpenAI is present in env for best results?
        # No, let's allow `langchain-chroma` to use its default if we don't pass `embedding_function`.
        # Wait, `Chroma(...)` from langchain-chroma REQUIRES `embedding_function` usually? 
        # Checking docs: "If not provided, it will look for 'sentence_transformers'..."
        
        try:
            from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
            return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        except ImportError:
            # Fallback to OpenAI if available?
            try:
                from langchain_openai import OpenAIEmbeddings
                return OpenAIEmbeddings()
            except:
                raise ImportError("No suitable embedding library found. Please install `sentence-transformers` or `langchain-openai`.")
        
    def ingest_text(self, 
                    text: str, 
                    chroma_config: ChromaNodeConfig, 
                    llm_profile: Optional[LLMProfile] = None,
                    dedup_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        if not text:
            return {"status": "skipped", "reason": "empty_text"}
            
        dedup_config = dedup_config or {}
        dedup_enabled = dedup_config.get("enabled", True)
        dedup_threshold = float(dedup_config.get("threshold", 0.95))
            
        # 1. Chunking
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.create_documents([text])
        
        # 2. Setup LLM for Smart Extraction
        if not llm_profile:
            llm_profile = get_first_profile()
            
        if llm_profile:
            dspy_lm = get_dspy_lm(llm_profile)
            extractor = dspy.ChainOfThought(ExtractEntities)
            
            # 3. Process Chunks (Smart Enrichment)
            for doc in docs:
                try:
                    with dspy.context(lm=dspy_lm):
                        pred = extractor(text=doc.page_content)
                        raw_entities = pred.entities
                        # Simple cleanup
                        entity_list = [e.strip() for e in raw_entities.split(",") if e.strip()]
                        if entity_list:
                            doc.metadata["entities"] = ", ".join(entity_list)
                except Exception as e:
                    logger.warning(f"Entity extraction failed for chunk: {e}")
        
        # 4. Store in Chroma
        client = self._get_client(chroma_config)
        chunks_to_upsert = []
        skipped_count = 0
        
        try:
             emb_fn = self._get_embedding_function()
             vectorstore = Chroma(
                 client=client, 
                 collection_name=chroma_config.collection_name, 
                 embedding_function=emb_fn
             )
             
             # --- SEMANTIC DEDUPLICATION ---
             if dedup_enabled:
                 # L2 Distance Threshold: dist = 2 * (1 - similarity)
                 # Sim 0.95 -> Dist 0.1
                 # Sim 0.99 -> Dist 0.02
                 limit_dist = 2 * (1 - dedup_threshold)
                 
                 for doc in docs:
                     # Search for closest EXISTING vector
                     # We use the vectorstore wrapper which handles embedding the query
                     results = vectorstore.similarity_search_with_score(doc.page_content, k=1)
                     
                     is_duplicate = False
                     if results:
                         existing_doc, score = results[0]
                         # Chroma default score is L2 distance. Lower = Closer.
                         if score < limit_dist:
                             is_duplicate = True
                             skipped_count += 1
                             # logger.debug(f"Semantic Dedup: Skipped chunk (Score {score:.4f} < {limit_dist:.4f})")
                     
                     if not is_duplicate:
                         chunks_to_upsert.append(doc)
             else:
                 chunks_to_upsert = docs
                 
        except Exception as e:
             logger.warning(f"Semantic Check/LangChain Init failed: {e}. Proceeding with ALL chunks (Native Fallback).")
             chunks_to_upsert = docs
             skipped_count = 0

        if not chunks_to_upsert:
             return {"status": "success_deduped_all", "chunks": 0, "skipped_chunks": skipped_count, "smart_extraction": bool(llm_profile)}

        # Native Upsert Logic
        coll = client.get_or_create_collection(chroma_config.collection_name)
        
        # Generate deterministic IDs using SHA256 of content
        import hashlib
        ids = []
        for d in chunks_to_upsert:
            content_hash = hashlib.sha256(d.page_content.encode('utf-8')).hexdigest()
            ids.append(f"id_{content_hash}")
            
        contents = [d.page_content for d in chunks_to_upsert]
        
        metas = []
        for d in chunks_to_upsert:
            m = d.metadata or {}
            if not m:
                m = {"source": "rag_ingest"}
            metas.append(m)
            
        coll.upsert(
            documents=contents,
            metadatas=metas,
            ids=ids
        )

        return {"status": "success", "chunks": len(chunks_to_upsert), "skipped_chunks": skipped_count, "smart_extraction": bool(llm_profile)}

    def search(self, 
               query: str, 
               chroma_config: ChromaNodeConfig, 
               llm_profile: Optional[LLMProfile] = None,
               k: int = 5) -> str:
        
        client = self._get_client(chroma_config)
        
        # 1. Smart Query Analysis (Entity Extraction)
        extracted_entities = []
        if not llm_profile:
            llm_profile = get_first_profile()

        if llm_profile:
             try:
                 dspy_lm = get_dspy_lm(llm_profile)
                 analyzer = dspy.ChainOfThought(ExtractQueryEntities)
                 with dspy.context(lm=dspy_lm):
                     pred = analyzer(query=query)
                     extracted_entities = [e.strip() for e in pred.entities.split(",") if e.strip()]
             except Exception as e:
                 logger.warning(f"Query analysis failed: {e}")

        # 2. Retrieval
        # Ideally we use metadata filtering if we found entities.
        # But broadly filtering by "contains" in comma-separated string is hard in Chroma basic metadata.
        # Chroma supports `where={"entities": {"$contains": "Value"}}`? No, standard is exact match or simple ops.
        # So "Hybrid" here means we might retrieve more (k*2) and re-rank or just standard retrieval for now.
        # We will stick to standard semantic search but retrieve slightly more to ensure recall.
        
        try:
            emb_fn = self._get_embedding_function()
            vectorstore = Chroma(
                client=client,
                collection_name=chroma_config.collection_name,
                embedding_function=emb_fn
            )
            # Fetch more if we want to filter in memory (Semantic Search)
            results = vectorstore.similarity_search(query, k=k)
            
            # Simple InMemory Re-ranking/Boosting if we have entities?
            if extracted_entities:
                # Naive boosting: Move doc to top if it contains entity in metadata
                filtered = []
                others = []
                for doc in results:
                    meta_ents = doc.metadata.get("entities", "").lower()
                    if any(e.lower() in meta_ents for e in extracted_entities):
                        filtered.append(doc)
                    else:
                        others.append(doc)
                results = filtered + others
            
        except Exception as e:
            logger.warning(f"LangChain Search failed: {e}. Native fallback.")
            coll = client.get_collection(chroma_config.collection_name)
            res = coll.query(query_texts=[query], n_results=k)
            # Flatten native format
            results = []
            if res['documents']:
                 # res['documents'] is list of list
                 docs = res['documents'][0]
                 metas = res['metadatas'][0] if res['metadatas'] else [{}] * len(docs)
                 for txt, meta in zip(docs, metas):
                     results.append(Document(page_content=txt, metadata=meta))

        # 3. Format Context
        context_parts = []
        for d in results[:k]:
            meta_str = f" [Entities: {d.metadata.get('entities','None')}]" if d.metadata.get("entities") else ""
            context_parts.append(f"---\n{d.page_content}{meta_str}")
            
        return "\n".join(context_parts)

    def get_collection_preview(self, chroma_config: ChromaNodeConfig, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        Get a preview of documents for the UI table.
        """
        try:
            client = self._get_client(chroma_config)
            # Check if collection exists first to avoid error?
            # get_collection raises ValueError if not found usually.
            try:
                coll = client.get_collection(chroma_config.collection_name)
            except Exception:
                return {"items": [], "total": 0, "error": "Collection not found"}

            count = coll.count()
            
            # Fetch docs
            # include=['metadatas', 'documents'] is default-ish but let's be explicit
            results = coll.get(
                limit=limit,
                offset=offset,
                include=["metadatas", "documents"]
            )
            
            items = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    items.append({
                        "id": results['ids'][i],
                        "excerpt": results['documents'][i][:200] + "..." if results['documents'][i] else "",
                        "metadata": results['metadatas'][i] or {},
                        # We don't have created_at usually unless we added it.
                    })
            
            return {
                "items": items,
                "total": count
            }
            
        except Exception as e:
            logger.error(f"Error listing collection: {e}")
            return {"items": [], "total": 0, "error": str(e)}

    def delete_collection(self, chroma_config: ChromaNodeConfig) -> Dict[str, Any]:
        """
        Delete a collection (Purge).
        """
        try:
            client = self._get_client(chroma_config)
            try:
                client.delete_collection(chroma_config.collection_name)
                return {"status": "success", "message": f"Collection '{chroma_config.collection_name}' deleted."}
            except ValueError:
                 return {"status": "error", "message": "Collection not found."}
            except Exception as e:
                 return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Client connection error: {str(e)}"}

