# Backend Nodes Technical Specification

## Overview
This directory (`backend/app/nodes`) contains the concrete implementations of the nodes used in the Agentic Graph.

## 1. Registry (`registry.py`)
Central mapping of "Frontend Node Types" to "Backend Python Classes".
```python
NODE_REGISTRY = {
    "agent": GenericAgentNode,
    "tool": ToolNode,
    "tool": ToolNode,
    "smart_node": SmartNode,
    "rag_node": RAGNode,
    # ...
}
```
*   **Usage**: Used by `compiler.py` to instantiate nodes dynamically.

## 2. Generic Agent (`agent.py`)

### `GenericAgentNode`
Standard ReAct-style agent.

#### `__init__(node_id: str, config: dict)`
*   `config`:
    *   `profile_id` (int): LLM Profile ID.
    *   `system_prompt` (str): Base instruction.
    *   `tools` (List[str]): Names of tools to bind.
    *   `max_iterations` (int): Loop protection.
    *   `flexible_mode` (bool): If True, requests JSON but allows free-form fields.

### `__call__(state: GraphState)`
*   **Logic**:
    1.  Hydrates LLM from `llm_factory`.
    2.  Binds tools found in `config['tools']` via `tool_registry`.
        *   **Virtual Tools**: Uses `tool_utils.create_virtual_tool` to bind other agents as tools.
    3.  Injects System Prompt (supports `{{ variable }}` templating from State).
    4.  Invokes LLM.
    5.  **Output Parsing**: Uses `text_processing.extract_json_from_text` to robustly handle JSON responses (even if wrapped in markdown).

    6.  **Anti-Hallucination & Robustness**:
        *   **Context Isolation**: If the agent is invoked as a tool (Sub-Agent), the Orchestrator's noisy history is replaced by a clean `HumanMessage(query)`.
        *   **Recursion Detection**: If the model tries to call *itself* as a tool, the call is intercepted, and a `SystemMessage` correction is injected to force a text response.
        *   **Hard Fallback**: After 3 failed attempts (persistent hallucination), forces a text response and clears invalid tool calls.
        *   **Polymorphic Return**: Returns `ToolMessage` if acting as a tool, `HumanMessage` if acting as a main agent.
        *   **Ollama Compatibility**: Uses `ollama_utils.adjust_messages_for_ollama` to convert Base64 `ToolMessage`s into Multimodal `HumanMessage`s (Visual Tokens) to fix context limits.

## 3. Tool Node (`tool_node.py`)

### `ToolNode`
Executes tools requested by the previous Agent message.

#### `__call__(state: GraphState, config: RunnableConfig)`
*   **Logic**:
    1.  Inspects `state['messages'][-1].tool_calls`.
    2.  Iterates through calls.
    3.  Fetches tool implementation from `app.services.tool_registry`.
    4.  Executes `tool.ainvoke(args)`.
    5.  Returns list of `ToolMessage` objects.
    6.  **Observability Trace**: Returns an explicit `output` dictionary containing `tools` (list of `{name, arguments, result}`) and `last_tool_input`/`output` for frontend Trace inspection.

## 4. Iterator Node (`iterator_node.py`)

### `IteratorNode`
Manages looping over a list of items.

#### `invoke(state: GraphState)`
*   **Logic**:
    1.  Reads input list from `state['context']` (Shared Blackboard).
    2.  Maintains an internal queue in `context` (e.g., `_iterator_queue_{id}`).
    3.  **State Update**: Writes the current item and updated queue to `context` (using overwrite reducer to prevent list explosion).
    4.  Returns `_signal="NEXT"` or `"COMPLETE"`.

## 6. RAG Node (`rag_node.py`)

### `RAGNode`
Smart Retrieval-Augmented Generation node with Read/Write capabilities.

#### `__init__(..., config: dict)`
*   `config`:
    *   `action` (str): "read" (default) or "write".
    *   `chroma` (dict): `ChromaNodeConfig` settings (`mode`, `path`/`host`, `collection`).

#### `__call__(state: GraphState)`
*   **Logic**:
    *   **Read**: Calls `rag_service.search`. Returns `SystemMessage` with context + `rag_context` key.
    *   **Write**: Calls `rag_service.ingest_text`. Returns status.
    *   **Inputs**: prioritized `state.get("query")` -> `state.get("content")` -> `messages[-1].content`.

## 7. Smart Node (`smart_node.py`)

### `SmartNode`
Advanced node using **DSPy** for optimizeable tasks ("Predict", "ChainOfThought").

#### `__init__(..., node_data: dict)`
*   `node_data`:
    *   `inputs` / `outputs`: List of `{name: str, desc: str}` defining the signature.
    *   `mode`: "Predict" or "ChainOfThought".
    *   `goal`: High-level instruction.
    *   `llm_profile`: Configuration for the specific LM to use.

#### `invoke(state: Dict)`
*   **Logic**:
    1.  **Input Mapping**: Extract inputs from `state` keys or auto-map from last message content.
    2.  **Signature Creation**: `dspy.make_signature` dynamic generation.
    3.  **Module Creation**: Instantiates `dspy.Predict` or `CoT`.
    4.  **Guardrails**: Wraps module in `dspy.Refine` if `guardrails` are configured (e.g. JSON format, Max Length).
    5.  **Loading**: Checks `resources/smart_nodes/` for a compiled version.
    6.  **Execution**: Runs within `dspy.context`.
    7.  **Return**: Updates state with output keys AND appends a `HumanMessage`.
    8.  **Token Usage**:
        *   Extracts usage from `dspy_lm.history` (LiteLLM/Ollama).
        *   **Fallback**: If provider reports 0 tokens, applies heuristic (1 token = 4 chars) by scanning history to ensure UI visibility.
