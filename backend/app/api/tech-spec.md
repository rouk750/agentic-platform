# Backend API Technical Specification

## Overview
RESTful API layer using FastAPI routers. Routes delegate to Service layer for business logic.

## Architecture Pattern
```
Router (HTTP) → Service (Business Logic) → Repository (Data Access)
```

Routes handle:
- Request/response validation (Pydantic schemas)
- HTTP status codes
- Dependency injection of services

## Directory Structure
```
api/
├── flows.py           # Flow CRUD + versioning
├── agent_templates.py # Template CRUD + versioning
├── settings.py        # LLM profile management
├── run.py             # WebSocket execution
└── jsonapi/           # JSON:API infrastructure
    ├── serializers.py
    ├── errors.py
    └── pagination.py
```

---

## Flow Routes (`flows.py`)
**Prefix:** `/api/flows`
**Service:** `FlowService`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/flows` | List flows (with `include_archived`, `skip`, `limit`) |
| GET | `/flows/{id}` | Get single flow |
| POST | `/flows` | Create flow |
| PUT | `/flows/{id}` | Update (auto-versions on data change) |
| DELETE | `/flows/{id}` | Delete with all versions |
| GET | `/flows/{id}/versions` | List versions |
| DELETE | `/flows/{id}/versions` | Bulk delete versions |
| DELETE | `/flows/{id}/versions/{vid}` | Delete single version |
| PUT | `/flows/{id}/versions/{vid}/lock` | Toggle lock |
| POST | `/flows/{id}/versions/{vid}/restore` | Restore version |

---

## Template Routes (`agent_templates.py`)
**Prefix:** `/api/agent-templates`
**Service:** `AgentTemplateService`

Same structure as Flow routes for CRUD and versioning operations.

---

## Settings Routes (`settings.py`)
**Prefix:** `/api/settings`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models` | List LLM profiles |
| POST | `/models` | Create profile (stores key in keyring) |
| PUT | `/models/{id}` | Update profile |
| DELETE | `/models/{id}` | Delete profile |
| POST | `/models/{id}/test` | Test existing profile |
| POST | `/test-connection` | Test transient params |
| GET | `/scan-ollama` | Auto-discover Ollama models |

---

## Run WebSocket (`run.py`)
**Endpoint:** `WS /api/run/ws/{graph_id}`

### Protocol
1. **Init**: Receive `{"graph": {...}, "input": "..."}`
2. **Compile**: Call `compile_graph` (thread pool)
3. **Stream Events**:
   - `token`: LLM partial output
   - `node_active/finished`: Node lifecycle
   - `tool_start/end`: Tool execution
   - `token_usage`: Per-step usage (automatic or manual fallback for SmartNodes)
   - `interrupt`: HITL breakpoint
   - `error`: Runtime exception
4. **Control**: `{"command": "resume"}` to continue

---

## JSON:API Layer (`jsonapi/`)
Optional response format controlled by `ENABLE_JSON_API` config.

### Components
- **Serializers**: Entity → JSON:API resource
- **Errors**: Exception → JSON:API error format
- **Pagination**: Offset and cursor-based

## Adherences
- **Services**: `FlowService`, `AgentTemplateService`
- **Exceptions**: Uses `app.exceptions` hierarchy
- **Logging**: Uses structured `app.logging`
