import asyncio
import json
import os
import shutil
import aiofiles
from contextlib import AsyncExitStack
from typing import Dict, List, Optional, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from app.logging import get_logger

logger = get_logger(__name__)


class MCPClientManager:
    """
    Manages connections to multiple MCP servers defined in configuration.
    """
    
    def __init__(self, config_path: str = "mcp_config.json"):
        # Resolve config path relative to backend root if needed
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(base_dir, config_path)
        
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self._tools_cache: Dict[str, List[Dict]] = {}

    async def initialize(self):
        """
        Reads config and establishes connections to all defined servers.
        """
        if not os.path.exists(self.config_path):
            logger.warning("mcp_config_not_found", path=self.config_path)
            return

        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                content = await f.read()
                config = json.loads(content)
        except Exception as e:
            logger.error("mcp_config_load_failed", error=str(e))
            return

        servers = config.get("mcpServers", {})
        
        for name, server_config in servers.items():
            try:
                if "url" in server_config:
                    await self.connect_sse(name, server_config)
                elif "command" in server_config:
                    await self.connect_stdio(name, server_config)
                else:
                    logger.warning("mcp_server_skipped", server=name, reason="No 'url' or 'command' found")
            except Exception as e:
                logger.error("mcp_server_connection_failed", server=name, error=str(e))

    async def connect_sse(self, name: str, config: Dict):
        url = config.get("url")
        headers = config.get("headers", {})
        
        logger.info("mcp_sse_connecting", server=name, url=url)
        try:
            transport = await self.exit_stack.enter_async_context(sse_client(url=url, headers=headers))
            read, write = transport
            
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            self.sessions[name] = session
            logger.info("mcp_sse_connected", server=name)
            await self._refresh_tools(name)
            
        except Exception as e:
            logger.error("mcp_sse_connection_failed", server=name, error=str(e))
            raise e

    async def connect_stdio(self, name: str, config: Dict):
        """
        Connects to a single MCP server via stdio.
        """
        command = config.get("command")
        args = config.get("args", [])
        env = config.get("env", {})
        
        # Merge with current env to ensure PATH is correct
        full_env = os.environ.copy()
        full_env.update(env)
        
        # Verify executable
        executable = await asyncio.to_thread(shutil.which, command)
        if not executable:
             logger.warning("mcp_executable_not_found", command=command, server=name)
             executable = command

        logger.info("mcp_stdio_connecting", server=name, command=executable)
        
        server_params = StdioServerParameters(
            command=executable,
            args=args,
            env=full_env
        )

        try:
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = transport
            
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            self.sessions[name] = session
            logger.info("mcp_stdio_connected", server=name)
            
            await self._refresh_tools(name)
            
        except Exception as e:
            logger.error("mcp_stdio_connection_failed", server=name, error=str(e))

    async def connect_server(self, name: str, config: Dict):
         # Backward compatibility wrapper or alias
         if "url" in config:
             await self.connect_sse(name, config)
         else:
             await self.connect_stdio(name, config)

    async def _refresh_tools(self, name: str):
        if name in self.sessions:
            try:
                result = await self.sessions[name].list_tools()
                self._tools_cache[name] = result.tools
                logger.info("mcp_tools_discovered", server=name, count=len(result.tools))
            except Exception as e:
                logger.error("mcp_tools_list_failed", server=name, error=str(e))

    def get_all_tools(self) -> List[Dict]:
        """
        Returns a flat list of all tools from all servers, enriched with server_name.
        """
        all_tools = []
        for server_name, tools in self._tools_cache.items():
            for tool in tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                    "server_name": server_name
                }
                all_tools.append(tool_dict)
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Any:
        if server_name not in self.sessions:
            raise ValueError(f"Server '{server_name}' not connected")
            
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        return result

    async def cleanup(self):
        await self.exit_stack.aclose()

