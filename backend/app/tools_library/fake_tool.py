
from langchain_core.tools import tool

@tool
def fake_tool() -> str:
    """
    A fake tool that returns a static string for testing purposes.
    """
    return "iit s a big fake"
