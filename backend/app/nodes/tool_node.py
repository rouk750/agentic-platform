from typing import Any, Dict, List
from langchain_core.messages import ToolMessage
from app.engine.state import GraphState
from app.services.tool_registry import list_tools_metadata, get_tool

from langchain_core.runnables import RunnableConfig

class ToolNode:
    def __init__(self, node_id: str, config: dict = None):
        self.node_id = node_id
        self.config = config or {}
        self.label = self.config.get("label", "Tool Node")
        
    async def __call__(self, state: GraphState, config: RunnableConfig) -> Dict[str, Any]:
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
                    output = await tool_instance.ainvoke(tool_args, config=config)
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
            
        # [FEATURE] Deep Observability: explicitly return the last tool's input/output
        # This allows the frontend to show "Input" and "Output" in the Trace tab
        # We define "output" as the last tool execution result for now, or a summary.
        trace_output = {
            "type": "tool_execution",
            "tools": [
                {
                    "name": tc['name'],
                    "arguments": tc['args'], 
                    "result": str(output) # Captures the last one, or could be a list
                } for tc in tool_calls
            ],
            # For simple single-tool view:
            "last_tool_input": tool_calls[-1]['args'] if tool_calls else {},
            "last_tool_output": str(output)
        }
            
        return {"messages": results, "last_sender": self.node_id, "output": trace_output}
