# Backend Engine Technical Specification

## Overview
This directory (`backend/app/engine`) is the "kernel" of the application. It handles the translation of the visual graph logic into executable code (LangGraph) and manages the execution state.

## 1. Graph Compilation (`compiler.py`)

### `compile_graph`
```python
def compile_graph(graph_data: Dict[str, Any], checkpointer: Optional[BaseCheckpointSaver] = None) -> StateGraph
```
Compiles a React Flow JSON graph into a LangGraph `StateGraph`.

**Logic Flow**:
1.  **Node Registration**: Iterates through `graph_data['nodes']`. Instantiates node classes from `app.nodes.registry` based on `node['type']`.
2.  **Configuration Injection**: Passes `node['data']` to the node constructor.
3.  **Adjacency Map**: Builds a map of `source -> targets` to handle branching.
4.  **Edge Processing**:
    *   **Tool Routing (`route_tool`)**:
        *   **Multi-Target Support**: Iterates over ALL `tool_calls` in the last message.
        *   **Parallel Execution**: If multiple calls target different agents, returns a list of Node IDs, triggering LangGraph's parallel fan-out.
        *   **Hybrid Routing (Fix)**:
            *   Routes explicitly named tool calls to Sub-Agents (Virtual Tools).
            *   **Fallback**: Routes unmatched tool calls (like `read_image`) to the generic `ToolNode` if available.
        *   **Implicit Binding**: populates `extra_tools_map` to ensure source agents bind to target agents (virtual tools) even if not explicitly configured.
    *   **Router Nodes**: If source is 'router', calls `make_router` logic.
    *   **Iterators**: Wiring up `NEXT` and `COMPLETE` handles.
    *   **Standard**: Simple `workflow.add_edge`.
5.  **Entry Point**: Detects start via `isStart` flag or orphan detection.
6.  **Human-in-the-Loop (HITL)**: Collects nodes with `require_approval=True` and passes them to `interrupt_before`.
7.  **Compilation**: Returns `workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt_nodes)`.

## 2. State Management (`state.py`)

### `GraphState` (TypedDict)
Defines the structure of the data passed between nodes.

| Field | Type | Description |
|-------|------|-------------|
| `messages` | `list[AnyMessage]` | Append-only execution log. Uses `langgraph.graph.message.add_messages` reducer to merge histories. |
| `inputs` | `dict` | Read-only copy of the initial flow inputs. |
| `context` | `dict` | Shared key-value store for cross-node data (variables). |
| `_signal` | `str` | Internal control signal (e.g., "NEXT", "COMPLETE") used by Iterator nodes. |

## 3. Router Logic (`router.py`)

### `make_router`
```python
def make_router(routes: List[Dict], handle_to_target: Dict[str, str], default_target: Optional[str], ...) -> Callable
```
Factory function that creates a customized routing function at runtime.

**Args**:
*   `routes`: List of conditions (e.g. `{"condition": "contains", "value": "error", "target_handle": "h1"}`).
*   `handle_to_target`: Maps UI handles to LangGraph Node IDs.

**Returns**:
*   A function `router(state) -> str` that checks `state['messages'][-1].content` or `state['context']` against the rules and returns the target Node ID.

### Supported Conditions
*   `contains`: Substring check.
*   `equals`: Exact match (case-insensitive).
*   `starts_with`: Prefix check.
*   `regex`: Regular expression match.

## 4. DSPy Integration

### `dspy_utils.py`

#### `get_dspy_lm`
```python
def get_dspy_lm(profile: LLMProfile) -> dspy.LM
```
Factory to create a DSPy-compatible LM client from our database `LLMProfile`.
*   **Supports**: OpenAI, Anthropic, Ollama, Azure, LMStudio.
*   **Logic**: Normalizes diverse keys/urls into the unified `dspy.LM` interface (DSPy 2.5+).

### `dspy_optimizer.py`

#### `optimize_node` (Async)
```python
async def optimize_node(request: OptimizationRequest, session: Session) -> OptimizationResponse
```
Runs the DSPy `BootstrapFewShot` optimizer to improve a prompt.

**Process**:
1.  **Dynamic Signature**: Creates a `dspy.Signature` on the fly based on `request.inputs` and `request.outputs`.
2.  **Dataset Construction**: Converts `request.examples` into `dspy.Example` objects.
3.  **Bootstrapping**: Runs the teacher model (same as student in this implementation) to generate rationales for the examples.
4.  **Compilation**: Saves the optimized JSON program to `resources/smart_nodes/`.
5.  **Return**: Path to the saved module.

## 5. Storage (`storage.py`)
*   **`get_sqlite_checkpointer`**: Returns a `SqliteSaver` connected to `checkpoints.sqlite` for persisting state definition.
