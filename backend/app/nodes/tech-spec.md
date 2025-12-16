# Backend Nodes Technical Specification

## Overview
This directory (`backend/app/nodes`) contains the concrete implementations of the nodes used in the Agentic Graph.

## 1. Registry (`registry.py`)
Central mapping of "Frontend Node Types" to "Backend Python Classes".
```python
NODE_REGISTRY = {
    "agent": GenericAgentNode,
    "tool": ToolNode,
    "smart_node": SmartNode,
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

#### `__call__(state: GraphState)`
*   **Logic**:
    1.  Hydrates LLM from `llm_factory`.
    2.  Binds tools found in `config['tools']` via `tool_registry`.
    3.  Injects System Prompt (supports `{{ variable }}` templating from State).
    4.  Invokes LLM.
    5.  **Output Processing**:
        *   If `tool_calls` exist: Returns `AIMessage` (triggers routing).
        *   Otherwise: Returns `HumanMessage` decorated with `### RESULT FROM {Label}` to separate it from internal thought chains.

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

## 4. Smart Node (`smart_node.py`)

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
