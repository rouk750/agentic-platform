# Backend Utils Technical Specification

## Overview
This directory (`backend/app/utils`) contains shared utility functions used across the application.

## 1. Observability (`observability_utils.py`)
Helpers for tracing and monitoring execution.

### `extract_node_id(event: Dict) -> Optional[str]`
*   **Purpose**: Reliably extracts the LangGraph Node ID from a raw event.
*   **Logic**: Checks `tags` (looking for `langgraph:node:...`) and falls back to `metadata`.

### `make_serializable(obj: Any) -> Any`
*   **Purpose**: Prepares arbitrary objects for JSON serialization over WebSocket.
*   **Logic**: Handles Pydantic models, LangChain messages, and generic objects with `__dict__`.

## 2. Text Processing (`text_processing.py`)
Helpers for string manipulation and LLM output parsing.

### `extract_json_from_text(text: str) -> Optional[Dict]`
*   **Purpose**: Robustly extracts JSON objects from LLM responses.
*   **Logic**:
    1.  Tries direct `json.loads`.
    2.  Regex search for `{...}` block.
    3.  Regex search for Markdown code blocks (` ```json ... ``` `).

### `sanitize_label(label: str) -> str`
*   **Purpose**: Converts user-friendly labels into safe identifiers (alphanumeric + underscores).

### `render_template(template: str, context: Dict) -> str`
*   **Purpose**: Simple Jinja2-style templating (`{{ variable }}`).

## 3. Tool Utilities (`tool_utils.py`)
Helpers for tool creation and management.

### `create_virtual_tool(name: str) -> StructuredTool`
*   **Purpose**: Creates a "Virtual Tool" that represents another Agent in the graph.
*   **Usage**: Used by `agent.py` when an agent is configured to call another agent (Sub-Agent pattern).
*   **Schema**: Generic `AgentInput(query: str)`.
