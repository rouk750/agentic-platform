"""
Tests for the exceptions module.
"""

import pytest
from app.exceptions import (
    AgenticPlatformError,
    GraphCompilationError,
    CyclicDependencyError,
    MaxRecursionDepthError,
    NodeExecutionError,
    MaxIterationsError,
    LLMConnectionError,
    LLMContextLengthError,
    ToolExecutionError,
    ToolNotFoundError,
    ResourceNotFoundError,
    ResourceLockedError,
    ValidationError,
)


class TestAgenticPlatformError:
    """Tests for the base exception class."""
    
    def test_basic_exception(self):
        exc = AgenticPlatformError("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
    
    def test_exception_with_details(self):
        exc = AgenticPlatformError("Error", details={"key": "value"})
        assert exc.details == {"key": "value"}
    
    def test_exception_with_cause(self):
        cause = ValueError("Original error")
        exc = AgenticPlatformError("Wrapped error", cause=cause)
        assert exc.cause is cause
        assert "caused by: Original error" in str(exc)
    
    def test_to_dict_json_api_format(self):
        exc = AgenticPlatformError("Test error", details={"foo": "bar"})
        result = exc.to_dict()
        
        assert result["status"] == "500"
        assert result["code"] == "INTERNAL_ERROR"
        assert result["title"] == "AgenticPlatformError"
        assert result["detail"] == "Test error"
        assert result["meta"] == {"foo": "bar"}


class TestGraphCompilationErrors:
    """Tests for graph compilation errors."""
    
    def test_basic_compilation_error(self):
        exc = GraphCompilationError("Failed to compile", node_id="node_1", node_type="agent")
        assert exc.status_code == 400
        assert exc.node_id == "node_1"
        assert exc.details["node_id"] == "node_1"
        assert exc.details["node_type"] == "agent"
    
    def test_cyclic_dependency_error(self):
        exc = CyclicDependencyError(flow_id="123")
        assert "Cyclic dependency" in exc.message
        assert "123" in exc.message
        assert exc.error_code == "CYCLIC_DEPENDENCY"
    
    def test_max_recursion_depth_error(self):
        exc = MaxRecursionDepthError(max_depth=5)
        assert "5" in exc.message
        assert exc.details["max_depth"] == 5


class TestNodeExecutionErrors:
    """Tests for node execution errors."""
    
    def test_node_execution_error(self):
        exc = NodeExecutionError("Execution failed", node_id="agent_1", node_type="agent")
        assert exc.node_id == "agent_1"
        assert exc.status_code == 500
    
    def test_max_iterations_error(self):
        exc = MaxIterationsError(node_id="loop_agent", max_iterations=10)
        assert "10" in exc.message
        assert "loop_agent" in exc.message


class TestLLMErrors:
    """Tests for LLM-related errors."""
    
    def test_llm_connection_error(self):
        exc = LLMConnectionError(provider="openai")
        assert exc.provider == "openai"
        assert exc.status_code == 502
        assert exc.details["provider"] == "openai"
    
    def test_context_length_error(self):
        exc = LLMContextLengthError()
        assert exc.status_code == 400
        assert "context" in exc.message.lower() or "history" in exc.message.lower()


class TestToolErrors:
    """Tests for tool-related errors."""
    
    def test_tool_execution_error(self):
        exc = ToolExecutionError(tool_name="read_file", message="Permission denied")
        assert exc.tool_name == "read_file"
        assert exc.details["tool_name"] == "read_file"
    
    def test_tool_not_found_error(self):
        exc = ToolNotFoundError(tool_name="unknown_tool")
        assert exc.status_code == 404
        assert "unknown_tool" in exc.message


class TestResourceErrors:
    """Tests for resource CRUD errors."""
    
    def test_resource_not_found(self):
        exc = ResourceNotFoundError(resource_type="Flow", resource_id=123)
        assert exc.status_code == 404
        assert "Flow" in exc.message
        assert "123" in exc.message
    
    def test_resource_locked(self):
        exc = ResourceLockedError(resource_type="FlowVersion", resource_id=456)
        assert exc.status_code == 423
        assert "locked" in exc.message.lower()
    
    def test_validation_error(self):
        exc = ValidationError("Invalid format", field="email")
        assert exc.status_code == 422
        assert exc.details["field"] == "email"
