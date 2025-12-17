# Frontend Store Technical Specification

## Overview
This directory (`frontend/src/store`) contains the global client-side state management using `zustand`.

## 1. Graph State (`graphStore.ts`)
Manages the nodes and edges for the **Flow Editor**.
*   **Dependencies**: `@xyflow/react` (for `applyNodeChanges`, `addEdge`, etc.).
*   **State**: `{ nodes: Node[], edges: Edge[] }`.
*   **Consumers**:
    *   `FlowEditor` (Renders graph).
    *   `ChatPanel` (Reads graph snapshot to send to Run API).
    *   `EditorSidebar` (Adds nodes).

## 2. Execution State (`runStore.ts`)
Manages the live execution session of an Agent.
*   **State**:
    *   `status`: 'idle' | 'connecting' | 'running' | 'paused' | 'done'.
    *   `messages`: Chat history (User/AI/Tool/Trace).
    *   `activeNodeId`: Currently executing node (for visual highlighting).
    *   `pausedNodeId`: Node ID where execution is paused (HITL).
    *   `nodeExecutionCounts`: Track loops.
*   **Adherences**:
    *   **Updated By**: `useAgentRuntime` (WebSocket events).
    *   **Consumed By**:
        *   `ChatPanel` (Renders messages).
        *   `AgentNode`, `ToolNode` (Visual "Green Border" highlighting).
        *   `FlowEditor` (Prevent editing while running?).

## 3. Persistent State (Future)
Currently, `GraphStore` is transient. A `PersistMiddleware` is recommended, or explicit Save/Load handling via API (currently managed in `FlowPage` via simple `useEffect` loading).
