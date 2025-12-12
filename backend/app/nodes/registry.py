from app.nodes.agent import GenericAgentNode
from app.nodes.tool_node import ToolNode
from app.nodes.rag_node import RAGNode
from app.nodes.router_node import RouterNode
from app.nodes.smart_node import SmartNode
from app.nodes.iterator_node import IteratorNode

# Mapping from React Flow node type (or internal type) to the python class/callable
NODE_REGISTRY = {
    "agent": GenericAgentNode,
    "tool": ToolNode,
    "rag": RAGNode,
    "router": RouterNode,
    "smart_node": SmartNode,
    "iterator": IteratorNode
}
