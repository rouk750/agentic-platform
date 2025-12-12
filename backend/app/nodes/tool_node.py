from typing import Any, Dict, List
from langchain_core.messages import ToolMessage
from app.engine.state import GraphState
from app.services.tool_registry import list_tools_metadata, get_tool

class ToolNode:
    def __init__(self, node_id: str, config: dict = None):
        self.node_id = node_id
        self.config = config or {}
        self.label = self.config.get("label", "Tool Node")
        
    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        """
        Executes tool calls from the last message.
        """
        messages = state['messages']
        last_message = messages[-1]
        
        if not hasattr(last_message, 'tool_calls'):
            # No tool calls to execute
            return {}
            
        tool_calls = last_message.tool_calls
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_call_id = tool_call['id']
            
            tool_instance = await get_tool(tool_name)
            
            if tool_instance:
                try:
                    # Execute tool - prefer async invoke
                    output = await tool_instance.ainvoke(tool_args)
                except Exception as e:
                    output = f"Error executing tool {tool_name}: {str(e)}"
            else:
                output = f"Error: Tool {tool_name} not found."
            
            from app.engine.debug import print_debug
            print_debug(f"DEBUG TOOL NODE {self.label} ({self.node_id})", {
                 "Tool": tool_name,
                 "Args": tool_args,
                 "Output": str(output)[:500]
            })

            results.append(ToolMessage(
                content=str(output),
                tool_call_id=tool_call_id,
                name=tool_name
            ))
            
        return {"messages": results, "last_sender": self.node_id}
