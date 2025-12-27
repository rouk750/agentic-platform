
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from app.engine.state import GraphState
from app.services.rag_service import RagService
from app.schemas.chroma_config import ChromaNodeConfig
from app.engine.debug import print_debug

class RAGNode:
    def __init__(self, node_id: str, config: dict = None):
        self.node_id = node_id
        self.config = config or {}
        
        # Parse Chroma Config from node config
        chroma_data = self.config.get('chroma', {})
        # Ensure default mode if not set
        if "mode" not in chroma_data:
             chroma_data["mode"] = "local"
             
        self.chroma_config = ChromaNodeConfig(**chroma_data)
        
        # Capabilities: read, write, or both (replaces action)
        # Backward compatibility: migrate action to capabilities
        if 'capabilities' in self.config:
            self.capabilities = self.config.get('capabilities', ['read'])
        elif 'action' in self.config:
            # Migration from old action format
            action = self.config.get('action', 'read')
            if action == 'read_write':
                self.capabilities = ['read', 'write']
            else:
                self.capabilities = [action]
        else:
            self.capabilities = ['read']  # Default
        
        # Global access: if True, tools are available to all agents in graph
        self.global_access = self.config.get('global_access', False)
        
        # Keep action for backward compatibility
        self.action = self.config.get('action', 'read')
        
        # Other configs
        self.k = self.config.get('k', 5)
        self.dedup_config = {
            "enabled": self.config.get("enable_dedup", True),
            "threshold": float(self.config.get("dedup_threshold", 0.95))
        }
        
        self.service = RagService()
    
    def get_tools(self):
        """
        Return the tools this RAG node exposes.
        Called by the compiler to register tools for agent binding.
        
        Returns:
            List of StructuredTool instances
        """
        from app.tools_library.rag_tools import create_rag_search_tool, create_rag_ingest_tool
        
        tools = []
        collection = self.chroma_config.collection_name
        
        if 'read' in self.capabilities:
            tools.append(create_rag_search_tool(
                collection_name=collection,
                chroma_config=self.chroma_config,
                default_k=self.k
            ))
        
        if 'write' in self.capabilities:
            tools.append(create_rag_ingest_tool(
                collection_name=collection,
                chroma_config=self.chroma_config,
                dedup_config=self.dedup_config
            ))
        
        return tools

    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """
        Executes RAG operation (Read or Write).
        """
        # Determine Input
        # Prefer explicit keys in state, fallback to last message
        input_text = state.get("query") or state.get("content")
        
        if not input_text:
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                # Check for Tool Calls (Agent-to-Node communication)
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        # If this node is the target (we assume the router sent us here because of the name match)
                        # We accept ANY tool call routed here, or we could check self.node_id/label equality if available.
                        # For now, just take the first valid query arg.
                        args = tc.get('args', {})
                        input_text = args.get('query') or args.get('content') or args.get('question')
                        if input_text:
                            break
                            
                # Fallback to content if no tool args found
                if not input_text:
                    input_text = last_msg.content
        
        if not input_text:
             return {"error": "RAGNode: No input provided (query/content keys, tool args, or last message empty)."}

        # Dynamic Action Detection
        # 1. Check if called via tool (tool name contains "ingest" -> write mode)
        # 2. Fall back to state override
        # 3. Fall back to configured action
        current_action = self.action
        tool_name = None
        
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    tool_name = tc.get('name', '')
                    if 'ingest' in tool_name.lower():
                        current_action = "write"
                        break
        
        # Allow explicit state override
        if "rag_action" in state:
            current_action = state["rag_action"]

        result = {}
        output_msg = ""
        
        print_debug(f"RAG NODE ({current_action})", {
            "mode": self.chroma_config.mode,
            "collection": self.chroma_config.collection_name,
            "input_preview": input_text[:50],
            "tool_name": tool_name
        })

        if current_action == "write":
            # Extract Semantic Dedup Config
            dedup_config = {
                "enabled": self.config.get("enable_dedup", True),
                "threshold": float(self.config.get("dedup_threshold", 0.95))
            }
            
            # Call Service Ingest
            res = self.service.ingest_text(str(input_text), self.chroma_config, dedup_config=dedup_config)
            result["rag_write_status"] = res
            
            # Deep Observer: Ingestion Details
            print_debug(f"RAG WRITE ({self.chroma_config.collection_name})", {
                "chunks_created": res.get("chunks"),
                "smart_extraction_active": res.get("smart_extraction"),
                "status": res.get("status"),
                "dedup_skipped": res.get("skipped_chunks", 0),
                "dedup_mode": "Semantic" if dedup_config["enabled"] else "Exact (SHA256)"
            })
            
            output_msg = f"RAG Write Completed. Status: {res.get('status')} (Chunks: {res.get('chunks')})"
            
        else: # read
            # Dynamic 'k' from config, default to 5
            k = self.config.get("k", 5)
            
            # Call Service Search
            context = self.service.search(str(input_text), self.chroma_config, k=k)
            result["rag_context"] = context
            
            # Deep Observer: Retrieval Details
            print_debug(f"RAG READ ({self.chroma_config.collection_name})", {
                "query": input_text[:100],
                "context_length": len(context),
                "context_preview": context[:200] + "..." if len(context) > 200 else context
            })
            
            # If used as a pure retrieval node, we might want to return context 
            # as a SystemMessage so the next node (Agent) sees it.
            # Or as a ToolMessage if it was called as a tool? 
            # Nodes in this graph usually output Messages.
            
            output_msg = f"### RAG RETRIEVAL CONTEXT ###\n{context}"
            
            # [CRITICAL] Output Format Handling
            # If we were called as a TOOL (by an Agent), we must return a ToolMessage.
            # Otherwise, the Agent will be left hanging with an open tool_call.
            
            messages = state.get("messages", [])
            last_msg = messages[-1] if messages else None
            tool_call_id = None
            
            if last_msg and hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                 # Assume the last tool call is for us. 
                 # In a perfect world we match names, but the Router sent us here.
                 tool_call_id = last_msg.tool_calls[-1].get('id')
            
            if tool_call_id:
                from langchain_core.messages import ToolMessage
                # Return ToolMessage to resolve the Agent's request
                return {
                    "messages": [ToolMessage(content=output_msg, tool_call_id=tool_call_id, name="rag_node")],
                    "rag_context": context,
                    "last_sender": self.node_id
                }
            
            # Default: SystemMessage (Pre-Prompt / Guard Pattern)
            return {
                "messages": [SystemMessage(content=output_msg)],
                "rag_context": context,
                "last_sender": self.node_id
            }

        # For Write, return a simplified message
        return {
            "messages": [SystemMessage(content=output_msg)],
            "last_sender": self.node_id,
            **result
        }
