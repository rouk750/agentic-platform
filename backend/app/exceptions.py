"""
Custom Exception Hierarchy for Agentic Platform Backend.

Provides structured error handling with JSON-serializable errors
for consistent API responses.
"""

from typing import Optional, Dict, Any


class AgenticPlatformError(Exception):
    """
    Base exception for all platform errors.
    
    Provides consistent structure for error handling and serialization.
    """
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self, 
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to JSON:API error format."""
        error = {
            "status": str(self.status_code),
            "code": self.error_code,
            "title": self.__class__.__name__,
            "detail": self.message,
        }
        if self.details:
            error["meta"] = self.details
        return error
    
    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


# ============================================================================
# Graph Compilation Errors
# ============================================================================

class GraphCompilationError(AgenticPlatformError):
    """Error during graph compilation from React Flow to LangGraph."""
    
    status_code = 400
    error_code = "GRAPH_COMPILATION_ERROR"
    
    def __init__(
        self, 
        message: str, 
        node_id: Optional[str] = None,
        node_type: Optional[str] = None,
        **kwargs
    ):
        details = {}
        if node_id:
            details["node_id"] = node_id
        if node_type:
            details["node_type"] = node_type
        super().__init__(message, details=details, **kwargs)
        self.node_id = node_id
        self.node_type = node_type


class CyclicDependencyError(GraphCompilationError):
    """Cyclic dependency detected in graph structure."""
    
    error_code = "CYCLIC_DEPENDENCY"
    
    def __init__(self, flow_id: str, **kwargs):
        super().__init__(
            f"Cyclic dependency detected: Flow contains a subgraph pointing to ancestor Flow ID {flow_id}",
            **kwargs
        )
        self.details["flow_id"] = flow_id


class MaxRecursionDepthError(GraphCompilationError):
    """Maximum recursion depth exceeded during compilation."""
    
    error_code = "MAX_RECURSION_DEPTH"
    
    def __init__(self, max_depth: int = 5, **kwargs):
        super().__init__(
            f"Maximum recursion depth reached for subgraphs ({max_depth}). Check for cyclic dependencies.",
            **kwargs
        )
        self.details["max_depth"] = max_depth


# ============================================================================
# Node Execution Errors
# ============================================================================

class NodeExecutionError(AgenticPlatformError):
    """Error during node execution."""
    
    status_code = 500
    error_code = "NODE_EXECUTION_ERROR"
    
    def __init__(
        self, 
        message: str, 
        node_id: str,
        node_type: Optional[str] = None,
        **kwargs
    ):
        details = {"node_id": node_id}
        if node_type:
            details["node_type"] = node_type
        super().__init__(message, details=details, **kwargs)
        self.node_id = node_id
        self.node_type = node_type


class MaxIterationsError(NodeExecutionError):
    """Agent node exceeded maximum iterations limit."""
    
    error_code = "MAX_ITERATIONS_EXCEEDED"
    
    def __init__(self, node_id: str, max_iterations: int, **kwargs):
        super().__init__(
            f"Agent '{node_id}' reached maximum iterations limit ({max_iterations})",
            node_id=node_id,
            **kwargs
        )
        self.details["max_iterations"] = max_iterations


# ============================================================================
# LLM Errors
# ============================================================================

class LLMError(AgenticPlatformError):
    """Base error for LLM-related issues."""
    
    status_code = 502
    error_code = "LLM_ERROR"


class LLMConnectionError(LLMError):
    """Failed to connect to LLM provider."""
    
    error_code = "LLM_CONNECTION_ERROR"
    
    def __init__(
        self, 
        provider: str, 
        message: str = "Failed to connect to LLM provider",
        **kwargs
    ):
        super().__init__(message, details={"provider": provider}, **kwargs)
        self.provider = provider


class LLMContextLengthError(LLMError):
    """Context length exceeded for LLM."""
    
    status_code = 400
    error_code = "CONTEXT_LENGTH_EXCEEDED"
    
    def __init__(self, **kwargs):
        super().__init__(
            "The conversation history is too long for the selected model. "
            "Try clearing the session or using a model with larger context window.",
            **kwargs
        )


class LLMRateLimitError(LLMError):
    """Rate limit exceeded for LLM provider."""
    
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    
    def __init__(self, provider: str, retry_after: Optional[int] = None, **kwargs):
        message = f"Rate limit exceeded for {provider}"
        if retry_after:
            message += f". Retry after {retry_after} seconds."
        super().__init__(message, details={"provider": provider}, **kwargs)
        if retry_after:
            self.details["retry_after"] = retry_after


# ============================================================================
# Tool Errors
# ============================================================================

class ToolExecutionError(AgenticPlatformError):
    """Error during tool execution."""
    
    status_code = 500
    error_code = "TOOL_EXECUTION_ERROR"
    
    def __init__(
        self, 
        tool_name: str, 
        message: str = "Tool execution failed",
        **kwargs
    ):
        super().__init__(message, details={"tool_name": tool_name}, **kwargs)
        self.tool_name = tool_name


class ToolNotFoundError(ToolExecutionError):
    """Requested tool not found in registry."""
    
    status_code = 404
    error_code = "TOOL_NOT_FOUND"
    
    def __init__(self, tool_name: str, **kwargs):
        super().__init__(
            tool_name=tool_name,
            message=f"Tool '{tool_name}' not found in registry",
            **kwargs
        )


# ============================================================================
# Resource Errors (CRUD)
# ============================================================================

class ResourceNotFoundError(AgenticPlatformError):
    """Requested resource not found."""
    
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    
    def __init__(
        self, 
        resource_type: str, 
        resource_id: Any,
        **kwargs
    ):
        super().__init__(
            f"{resource_type} with ID {resource_id} not found",
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
            **kwargs
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceLockedError(AgenticPlatformError):
    """Resource is locked and cannot be modified."""
    
    status_code = 423
    error_code = "RESOURCE_LOCKED"
    
    def __init__(
        self, 
        resource_type: str, 
        resource_id: Any,
        **kwargs
    ):
        super().__init__(
            f"{resource_type} {resource_id} is locked and cannot be modified",
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
            **kwargs
        )


class ValidationError(AgenticPlatformError):
    """Input validation failed."""
    
    status_code = 422
    error_code = "VALIDATION_ERROR"
    
    def __init__(
        self, 
        message: str,
        field: Optional[str] = None,
        **kwargs
    ):
        details = {}
        if field:
            details["field"] = field
        super().__init__(message, details=details, **kwargs)


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigurationError(AgenticPlatformError):
    """Invalid configuration."""
    
    status_code = 500
    error_code = "CONFIGURATION_ERROR"
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details=details, **kwargs)
