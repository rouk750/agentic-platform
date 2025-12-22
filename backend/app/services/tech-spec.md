# Backend Services Technical Specification

## Overview
Business logic layer implementing the Service pattern. Services encapsulate domain operations and delegate data access to Repositories.

## Architecture
```
API Routes → Services → Repositories → Database
                ↓
           Exceptions (domain errors)
```

## Directory Structure
```
services/
├── flow_service.py      # Flow business logic
├── template_service.py  # AgentTemplate business logic
├── llm_factory.py       # LLM instance creation
├── tool_registry.py     # Tool discovery & registry
├── mcp_client.py        # MCP server connections
└── security.py          # Keyring operations
```

---

## FlowService (`flow_service.py`)

Business logic for Flow entities with automatic versioning.

| Method | Signature | Description |
|--------|-----------|-------------|
| `list_flows` | `(skip, limit, include_archived)` | Paginated list |
| `get_flow` | `(flow_id) → Flow` | Get or raise `ResourceNotFoundError` |
| `create_flow` | `(FlowCreate) → Flow` | Create with timestamps |
| `update_flow` | `(id, FlowUpdate) → Flow` | Update, auto-version if data changes |
| `delete_flow` | `(id)` | Cascade delete with versions |
| `list_versions` | `(flow_id)` | Ordered by created_at desc |
| `restore_version` | `(flow_id, version_id)` | Restore flow data |
| `delete_version` | `(flow_id, version_id)` | With lock/active checks |
| `toggle_version_lock` | `(flow_id, version_id, is_locked)` | Lock/unlock |

### Dependencies
- `FlowRepository`, `FlowVersionRepository`
- `app.exceptions` (ResourceNotFoundError, ResourceLockedError, ValidationError)
- `app.logging`

---

## AgentTemplateService (`template_service.py`)

Same pattern as FlowService for AgentTemplate entities.

---

## LLM Factory (`llm_factory.py`)

Creates LangChain LLM instances from database profiles.

| Method | Description |
|--------|-------------|
| `get_llm_profile(id)` | Fetch profile from DB |
| `create_llm_instance(profile)` | Decrypt key, create LLM |
| `get_model(id)` | **Cached** wrapper (LRU) returning ready-to-use LLM |
| `invalidate_model_cache()` | Clear LLM cache |

### Supported Providers
OpenAI, Anthropic, Mistral, Ollama, Azure, LMStudio

---

## Tool Registry (`tool_registry.py`)

Singleton registry for local and MCP tools.

| Method | Description |
|--------|-------------|
| `load_tools()` | Scan tools_library + init MCP |
| `get_tool(id)` | Get executable tool |
| `list_tools_metadata()` | JSON for frontend UI |

---

## MCP Client (`mcp_client.py`)

Model Context Protocol server connections.

| Method | Description |
|--------|-------------|
| `initialize()` | Load config, connect servers |
| `get_all_tools()` | Aggregate from all servers |
| `call_tool(server, tool, args)` | Proxy execution |

### Features
- Non-blocking I/O with `aiofiles`
- Output truncation (50k chars)
- Dynamic Pydantic schema generation
- Ollama-compatible schemas

---

## Security (`security.py`)

OS keyring wrapper for API key storage.

| Method | Description |
|--------|-------------|
| `save_api_key(key) → ref` | Store, return UUID reference |
| `get_api_key(ref) → key` | Retrieve plaintext |

---

## Exception Hierarchy

Services raise domain-specific exceptions (defined in `app/exceptions.py`):

| Exception | HTTP | Usage |
|-----------|------|-------|
| `ResourceNotFoundError` | 404 | Entity not found |
| `ResourceLockedError` | 423 | Version is locked |
| `ValidationError` | 400 | Business rule violation |
| `LLMConnectionError` | 502 | Provider unreachable |

## Adherences
- **Repositories**: `app.repositories.*`
- **API Layer**: `app.api.*` routes inject services
- **Config**: `app.config.settings`
