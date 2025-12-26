"""
Engine Commands Package

Command pattern implementation for graph compilation.

Usage:
    from app.engine.commands import get_compile_command, CompileContext
    
    command = get_compile_command('agent')
    if command:
        command.execute(node_id, node_data, context)
"""

from app.engine.commands.base import (
    BaseCompileCommand,
    CompileContext,
)
from app.engine.commands.registry import (
    CommandRegistry,
    get_command_registry,
    get_compile_command,
)
from app.engine.commands.compile_agent import CompileAgentCommand
from app.engine.commands.compile_tool import CompileToolCommand
from app.engine.commands.compile_iterator import CompileIteratorCommand
from app.engine.commands.compile_smart import CompileSmartNodeCommand
from app.engine.commands.compile_subgraph import CompileSubgraphCommand
from app.engine.commands.compile_router import CompileRouterCommand

__all__ = [
    # Base
    "BaseCompileCommand",
    "CompileContext",
    # Registry
    "CommandRegistry",
    "get_command_registry",
    "get_compile_command",
    # Commands
    "CompileAgentCommand",
    "CompileToolCommand",
    "CompileIteratorCommand",
    "CompileSmartNodeCommand",
    "CompileSubgraphCommand",
    "CompileRouterCommand",
]
