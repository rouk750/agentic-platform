# Backend API Technical Specification

## Overview
This directory (`backend/app/api`) contains the **FastAPI** routers.

## 1. Settings Router (`settings.py`)
`Prefix: /api/settings`

### `POST /models`
```python
def create_model_profile(profile: LLMProfileCreate, session: Session) -> LLMProfile
```
 Creates a new LLM configuration.
- **Side Effects**: Saves API key securely to system keyring using `save_api_key`.

### `GET /models`
```python
def list_model_profiles(session: Session) -> List[LLMProfile]
```
Lists all saved profiles.
- **Note**: Does not return sensitive API keys manifest, only `api_key_ref`.

### `POST /models/{model_id}/test`
```python
async def test_saved_model_connection(model_id: int, session: Session) -> dict
```
Verifies an *existing* DB profile works.
- **Logic**: Decrypts key using `get_api_key` and calls provider's `test_connection`.

### `POST /test-connection`
```python
async def test_connection(request: TestConnectionRequest) -> dict
```
Verifies transient connection parameters (before saving).

## 2. Flows Router (`flows.py`)
`Prefix: /api/flows`

### `GET /flows`
```python
def read_flows(session: Session) -> List[FlowRead]
```

### `POST /flows`
```python
def create_flow(flow_in: FlowCreate, session: Session) -> FlowRead
```
Saves a new workflow.

### `PUT /flows/{flow_id}`
```python
def update_flow(flow_id: int, flow_update: FlowUpdate, session: Session) -> FlowRead
```
Updates flow data.
- **Logic**: If `data` (graph structure) changes, automatically creates a `FlowVersion`.

### `DELETE /flows/{flow_id}/versions`
```python
def delete_flow_versions(flow_id: int, version_ids: List[int] = Body(...), session: Session) -> dict
```
Bulk deletes specific versions of a flow.
- **Payload**: JSON list of version IDs `[1, 2, 3]`.
- **Validation**: Cannot delete locked versions or the current active version.

### `PUT /flows/{flow_id}/versions/{version_id}/lock`
```python
def toggle_flow_version_lock(flow_id: int, version_id: int, is_locked: bool, session: Session) -> FlowVersionRead
```
Toggles the lock status of a version.

### `POST /flows/{flow_id}/versions/{version_id}/restore`
```python
def restore_flow_version(flow_id: int, version_id: int, session: Session) -> FlowRead
```
Reverts current data to a previous version.

### `GET /flows/{flow_id}/versions`
```python
def read_flow_versions(flow_id: int, session: Session) -> List[FlowVersionRead]
```

## 3. Run Router (`run.py`)
`Prefix: /api/run`

### `WS /ws/run/{graph_id}`
```python
async def websocket_endpoint(websocket: WebSocket, graph_id: str)
```
Handles streaming execution of agents.
**Protocol**:
1.  **Init**: Recv JSON `{"graph": {...}, "input": "..."}`.
2.  **Compile**: Calls `app.engine.compiler.compile_graph`.
3.  **Stream**: Loops `app.astream_events` (version="v2").
    *   **Recursion Limit**: Configurable via `LANGGRAPH_RECURSION_LIMIT` (default 50).
    *   `token`: LLM partial output.
    *   `node_active`: Logic node start.
    *   `node_finished`: Node output (includes `has_tool_calls` flag and verification results).
    *   `tool_start/end`: Tool execution details (includes `node_id` of the caller).
    *   `token_usage`: (New) Sent on `on_chat_model_end`. Payload: `{type: "token_usage", node_id: "...", usage: {input_tokens: N, output_tokens: N, total_tokens: N}}`.
    *   `interrupt`: Sent when execution pauses at a breakpoint (HITL). Payload: `{type: "interrupt", node_id: "..."}`.
    *   `error`: Sent on runtime exceptions. Payload: `{type: "error", message: "..."}`.
        *   **Context Errors**: Returns a structured friendly message if context length is exceeded.
4.  **Control Commands**:
    *   **Resume**: Client sends `{"command": "resume"}` to continue execution from a paused state.

## 4. Agent Templates (`agent_templates.py`)
`Prefix: /api/agent-templates`

### `PUT /agent-templates/{id}`
```python
def update_agent_template(template_id: int, template_update: AgentTemplateUpdate, session: Session) -> AgentTemplateRead
```
Updates template config.
- **Logic**: Increments version number on config change.

### `POST /{id}/versions/{vid}/restore`
```python
def restore_agent_template_version(...) -> AgentTemplateRead
```
Reverts current config to a previous version.

### `DELETE /agent-templates/{template_id}/versions`
```python
def delete_agent_template_versions(template_id: int, version_ids: List[int] = Body(...), session: Session) -> dict
```
Bulk deletes specific versions.
- **Validation**: Cannot delete locked versions or the current active version.

### `PUT /agent-templates/{template_id}/versions/{version_id}/lock`
```python
def toggle_agent_template_version_lock(template_id: int, version_id: int, is_locked: bool, session: Session) -> AgentTemplateVersionRead
```
Toggles the lock status of a version.
