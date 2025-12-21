from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Callable

def create_virtual_tool(name: str) -> StructuredTool:
    """
    Creates a virtual tool wrapper for an agent that is not in the registry.
    This allows the LLM to call another agent as if it were a tool.
    """
    # Define a generic input schema for talking to another agent
    class AgentInput(BaseModel):
        query: str = Field(description="The full message or query to send to the agent.")

    def call_virtual_agent(query: str):
        # The actual routing is handled by the graph edge logic, not this function.
        # This return value is just a placeholder.
        return f"Routing to agent {name}..."

    return StructuredTool.from_function(
        func=call_virtual_agent,
        name=name,
        description=f"Send a message or query to the agent named '{name}'. Use this to delegate tasks.",
        args_schema=AgentInput
    )
