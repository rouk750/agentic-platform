"""
Command Registry

Central registry for all compilation commands.
Provides factory pattern for getting the right command for each node type.
"""

from typing import Dict, Type, Optional

from app.engine.commands.base import BaseCompileCommand, CompileContext
from app.engine.commands.compile_agent import CompileAgentCommand
from app.engine.commands.compile_tool import CompileToolCommand
from app.engine.commands.compile_iterator import CompileIteratorCommand
from app.engine.commands.compile_smart import CompileSmartNodeCommand
from app.engine.commands.compile_subgraph import CompileSubgraphCommand
from app.engine.commands.compile_router import CompileRouterCommand
from app.logging import get_logger

logger = get_logger(__name__)


class CommandRegistry:
    """
    Registry of compilation commands indexed by node type.
    
    Uses singleton pattern - commands are instantiated once and reused.
    """
    
    _instance: Optional['CommandRegistry'] = None
    _commands: Dict[str, BaseCompileCommand] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Register all built-in commands."""
        self.register(CompileAgentCommand())
        self.register(CompileToolCommand())
        self.register(CompileIteratorCommand())
        self.register(CompileSmartNodeCommand())
        self.register(CompileSubgraphCommand())
        self.register(CompileRouterCommand())
        
        logger.debug("command_registry_initialized", commands=list(self._commands.keys()))
    
    def register(self, command: BaseCompileCommand):
        """
        Register a command for its node types.
        
        Args:
            command: Command instance to register
        """
        for node_type in command.node_types:
            self._commands[node_type] = command
    
    def get(self, node_type: str) -> Optional[BaseCompileCommand]:
        """
        Get command for a node type.
        
        Args:
            node_type: The node type (e.g., 'agent', 'tool')
            
        Returns:
            Command if found, None otherwise
        """
        return self._commands.get(node_type)
    
    def has(self, node_type: str) -> bool:
        """Check if a command exists for the node type."""
        return node_type in self._commands
    
    @property
    def supported_types(self) -> list:
        """Get list of all supported node types."""
        return list(self._commands.keys())


# Global singleton instance
_registry: Optional[CommandRegistry] = None


def get_command_registry() -> CommandRegistry:
    """Get the global command registry singleton."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry


def get_compile_command(node_type: str) -> Optional[BaseCompileCommand]:
    """
    Convenience function to get command for a node type.
    
    Args:
        node_type: The node type
        
    Returns:
        Command if found, None otherwise
    """
    return get_command_registry().get(node_type)
