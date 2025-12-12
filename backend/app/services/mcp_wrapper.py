from typing import Optional, Type, Any, Dict, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, create_model, Field

from app.services.mcp_client import MCPClientManager

class MCPLangChainTool(BaseTool):
    """
    A LangChain-compatible tool that forwards calls to an MCP server.
    """
    client_manager: MCPClientManager
    server_name: str
    tool_name: str
    
    # We dynamically generate args_schema based on MCP schema
    
    def __init__(self, client_manager: MCPClientManager, server_name: str, tool_data: Dict):
        # Construct current tool name
        # To avoid collisions, we might prefix it: mcp__server__tool
        name = f"mcp__{server_name}__{tool_data['name']}"
        description = tool_data.get("description", f"MCP Tool {tool_data['name']} from {server_name}")
        
        # 1. Convert MCP JSON Schema to Pydantic Model for validation
        input_schema = tool_data.get("input_schema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        fields = {}
        for prop_name, prop_schema in properties.items():
            # Simplification: mapping basic types. 
            # In a robust implementation, we'd do a recursive conversion.
            prop_type = Any
            schema_type = prop_schema.get("type")
            
            if schema_type == "string":
                prop_type = str
            elif schema_type == "integer":
                prop_type = int
            elif schema_type == "number":
                prop_type = float
            elif schema_type == "boolean":
                prop_type = bool
            elif schema_type == "array":
                prop_type = List[Any]
            elif schema_type == "object":
                prop_type = Dict[str, Any]
                
            default = ... if prop_name in required else None
            # Handle explicit default in schema if present
            if "default" in prop_schema:
                default = prop_schema["default"]
                
            fields[prop_name] = (prop_type, Field(default=default, description=prop_schema.get("description")))
            
        args_schema = create_model(f"{name}Schema", **fields)
        
        super().__init__(
            name=name,
            description=description,
            args_schema=args_schema,
            client_manager=client_manager,
            server_name=server_name,
            tool_name=tool_data['name']
        )

    def _run(self, **kwargs: Any) -> Any:
        """
        Executes the tool by calling the MCP client.
        We need to run this async, but LangChain _run is sync.
        We should implement _arun ideally, or use a sync bridge.
        """
        # Since we are in an async context (FastAPI), we should prioritize _arun.
        # But if LangGraph calls _run, we might fail.
        # Let's try to block if definitely needed, or rely on _arun.
        print(f"CRITICAL ERROR: MCPLangChainTool._run (sync) was called for {self.tool_name}. This tool only supports async.")
        raise NotImplementedError("This tool only supports async execution via _arun")

    async def _arun(self, **kwargs: Any) -> Any:
        """
        Async execution of the tool.
        """
        print(f"DEBUG: Executing MCP Tool {self.server_name}/{self.tool_name} with args: {kwargs}")
        try:
            result = await self.client_manager.call_tool(
                self.server_name,
                self.tool_name,
                kwargs
            )
            
            # MCP Result object handling
            # It has content: List[TextContent | ImageContent | ...]
            output = []
            if hasattr(result, 'content'):
                for item in result.content:
                    if item.type == 'text':
                        output.append(item.text)
                    elif item.type == 'image':
                        output.append(f"[Image: {item.mimeType}]")
                    else:
                        output.append(str(item))
            else:
                output.append(str(result))
            
            final_output = "\n".join(output)
            print(f"DEBUG: MCP Tool {self.tool_name} success. Output len: {len(final_output)}")
            return final_output
            
        except Exception as e:
            error_msg = f"Error executing MCP tool {self.tool_name}: {e}"
            print(f"ERROR: {error_msg}")
            # Identify if it's a validation error usually caused by bad args
            return error_msg
