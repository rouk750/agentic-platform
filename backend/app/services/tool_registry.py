import importlib
import inspect
import pkgutil
import os
import asyncio
from typing import Dict, List, Any
from langchain_core.tools import BaseTool
from langchain_core.tools import StructuredTool

from app.services.mcp_client import MCPClientManager
from app.services.mcp_wrapper import MCPLangChainTool
from app.logging import get_logger

logger = get_logger(__name__)

# We will store tools here
# Map: tool_name -> tool_instance
_TOOL_REGISTRY: Dict[str, BaseTool] = {}
_MCP_MANAGER: MCPClientManager | None = None

async def load_tools():
    """
    Scans the 'app.tools_library' package for tools AND loads MCP tools.
    """
    global _TOOL_REGISTRY, _MCP_MANAGER
    
    # 1. Load Local Tools
    package_name = "app.tools_library"
    import app.tools_library
    package_path = os.path.dirname(app.tools_library.__file__)
    
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        full_module_name = f"{package_name}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                    try:
                        instance = obj()
                        _TOOL_REGISTRY[instance.name] = instance
                    except Exception as e:
                       logger.debug("skipping_class_tool", tool_name=name, error=str(e))

                if isinstance(obj, StructuredTool):
                    _TOOL_REGISTRY[obj.name] = obj
        except Exception as e:
            logger.error("module_load_failed", module=full_module_name, error=str(e))

    # 2. Load MCP Tools
    try:
        if _MCP_MANAGER is None:
            _MCP_MANAGER = MCPClientManager()
            await _MCP_MANAGER.initialize()
            
        mcp_tools = _MCP_MANAGER.get_all_tools()
        for tool_data in mcp_tools:
            try:
                wrapper = MCPLangChainTool(
                    client_manager=_MCP_MANAGER,
                    server_name=tool_data['server_name'],
                    tool_data=tool_data
                )
                _TOOL_REGISTRY[wrapper.name] = wrapper
            except Exception as e:
                logger.error("mcp_tool_wrap_failed", tool_name=tool_data.get('name'), error=str(e))
    except Exception as e:
        logger.warning("mcp_initialization_failed", error=str(e))
        # Continue so local tools are still available

    logger.info("tools_loaded", count=len(_TOOL_REGISTRY), tools=list(_TOOL_REGISTRY.keys()))


async def cleanup_tools():
    global _MCP_MANAGER
    if _MCP_MANAGER:
        await _MCP_MANAGER.cleanup()

async def list_tools_metadata() -> List[Dict[str, str]]:
    if not _TOOL_REGISTRY:
        await load_tools()
        
    result = []
    for name, tool in _TOOL_REGISTRY.items():
        result.append({
            "id": name,
            "name": name,
            "description": tool.description,
            "type": "tool"
        })
    return result

async def get_tool(tool_id: str) -> BaseTool | None:
    if not _TOOL_REGISTRY:
        await load_tools()
    return _TOOL_REGISTRY.get(tool_id)

