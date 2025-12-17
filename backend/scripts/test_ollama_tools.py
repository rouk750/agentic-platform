import asyncio
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

@tool
def magic_number_tool(input: str) -> str:
    """Returns the magic number."""
    return "42"

async def test():
    llm = ChatOllama(model="llama3.1:8b", temperature=0) # Using existing model
    llm_with_tools = llm.bind_tools([magic_number_tool])
    
    msg = HumanMessage(content="What is the magic number?")
    print("Invoking...")
    res = await llm_with_tools.ainvoke([msg])
    print("Result content:", res.content)
    print("Tool calls:", res.tool_calls)

if __name__ == "__main__":
    asyncio.run(test())
