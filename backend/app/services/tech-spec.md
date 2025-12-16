# Backend Services Technical Specification

## Overview
This directory (`backend/app/services`) contains the core business logic services.

## 1. LLM Factory (`llm_factory.py`)

### `get_llm_profile(profile_id: int) -> LLMProfile`
Retrieves a profile from the database.

### `create_llm_instance(profile: LLMProfile) -> BaseChatModel`
*   **Logic**:
    1.  Decrypts API key from keyring (if `api_key_ref` is present).
    2.  Calls `LLMProviderFactory.create`.
    3.  Returns a configured LangChain object.

## 2. Tool Registry (`tool_registry.py`)
Singleton registry for all available tools (Local + MCP).

### `load_tools()` (Async)
*   Scans `app.tools_library` for subclasses of `BaseTool`.
*   Initializes `MCPClientManager` and wraps MCP tools.

### `get_tool(tool_id: str) -> BaseTool`
*   Returns the executable tool instance.

### `list_tools_metadata() -> List[Dict]`
*   Returns JSON-friendly list of tools for Frontend UI.

## 3. MCP Client Manager (`mcp_client.py`)
Manages connections to Model Context Protocol servers.

### `MCPClientManager`
#### `initialize()`
*   Reads `mcp_config.json`.
*   Establishes connections (SSE or Stdio).

#### `get_all_tools() -> List[Dict]`
*   Aggregates tools from all connected sessions.

#### `call_tool(server_name, tool_name, arguments)`
*   Proxies execution to the remote server.

## 4. Security (`security.py`)
System Keyring wrapper.

### `save_api_key(api_key: str) -> str`
*   **Returns**: A UUID `key_ref`.
*   **Side Effect**: Stores key in OS Keyring (e.g., Keychain on macOS).

### `get_api_key(key_ref: str) -> str`
*   Retrieves the plaintext key.
