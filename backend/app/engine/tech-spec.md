# Backend Engine Technical Specification

## Overview
The engine is the "kernel" of the application. It compiles visual graphs into executable LangGraph workflows and manages execution state.

## Directory Structure
```
engine/
├── compiler.py       # Graph → LangGraph compilation
├── state.py          # GraphState definition
├── router.py         # Dynamic routing logic
├── storage.py        # Checkpoint persistence
├── commands/         # Command pattern for node compilation
│   ├── base.py       # BaseCompileCommand
│   ├── compile_agent.py
│   ├── compile_tool.py
│   ├── compile_iterator.py
│   └── registry.py   # CommandRegistry
├── observers/        # Event observer pattern
│   ├── event_types.py # Typed events
│   ├── base.py       # BaseObserver, ObserverManager
│   └── websocket_observer.py
└── dspy_*.py         # DSPy optimization modules
```

---

## Graph Compilation (`compiler.py`)

### `compile_graph(graph_data, checkpointer=None) -> StateGraph`
Compiles React Flow JSON into LangGraph StateGraph.

**Process:**
1. **Node Indexing**: O(1) lookup via dictionary map
2. **Command Pattern**: Delegates to `CommandRegistry` for node compilation
3. **Edge Processing**: Tool routing, router nodes, iterator wiring
4. **Entry Point**: Detected via `isStart` flag or orphan detection
5. **HITL**: Collects `require_approval=True` nodes for `interrupt_before`

---

## Command Pattern (`commands/`)

Encapsulates node compilation logic for maintainability.

| Command | Description |
|---------|-------------|
| `CompileAgentCommand` | Agent nodes with tool injection |
| `CompileToolCommand` | Tool execution nodes |
| `CompileIteratorCommand` | Loop control nodes |
| `CompileRouterCommand` | Conditional routing |
| `CompileSubgraphCommand` | Nested flow nodes |

### Usage
```python
registry = CommandRegistry()
command = registry.get_command(node_type)
command.execute(context)
```

---

## Observer Pattern (`observers/`)

Decoupled event handling for engine execution.

### Event Types (`event_types.py`)
| Event | Description |
|-------|-------------|
| `TokenEvent` | LLM token streamed |
| `NodeActiveEvent` | Node started |
| `NodeFinishedEvent` | Node completed |
| `ToolStartEvent/EndEvent` | Tool execution |
| `TokenUsageEvent` | Token statistics |
| `InterruptEvent` | HITL pause |
| `ErrorEvent` | Execution error |

### ObserverManager
```python
manager = ObserverManager()
manager.register(WebSocketObserver(websocket))
await manager.notify(TokenEvent(content="Hello"))
```

---

## State Management (`state.py`)

### `GraphState` (TypedDict)
| Field | Type | Description |
|-------|------|-------------|
| `messages` | `list[AnyMessage]` | Append-only execution log |
| `inputs` | `dict` | Initial flow inputs |
| `context` | `dict` | Cross-node variable store. **Reducers**: Overwrites keys (including lists) to prevent duplication loops. |
| `_signal` | `str` | Iterator control signal |

---

## Router Logic (`router.py`)

### `make_router(routes, handle_to_target, default_target) -> Callable`
Creates dynamic routing function at runtime.

**Supported Conditions:**
- `contains`, `equals`, `starts_with`, `regex`

---

## DSPy Integration

| Module | Description |
|--------|-------------|
| `dspy_utils.py` | LM factory from LLMProfile |
| `dspy_optimizer.py` | BootstrapFewShot optimization |
| `dspy_modules.py` | Custom DSPy modules |

---

## Adherences
- **API Layer**: `api/run.py` uses observers for WebSocket streaming
- **Logging**: Uses structured `app.logging`
- **Retry**: LLM calls use `app.utils.retry` decorators
