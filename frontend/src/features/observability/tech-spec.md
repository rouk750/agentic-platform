# Deep Observability Technical Specification

## Overview
This feature (`frontend/src/features/observability`) provides a comprehensive debugging and inspection console for Agentic executions.

## 1. Deep Observability Page (`DeepObservabilityPage.tsx`)
*   **Route**: `/debug/:runId`
*   **Layout**: 3-Pane Resizable Layout.
    1.  **Timeline**: Chronological list of execution steps.
    2.  **Inspector**: Detailed view of the selected step state.
    3.  **Playground**: Isolated runtime for testing prompts/inputs on a specific node.

## 2. Components

### `ExecutionTimeline.tsx`
*   **Purpose**: Visualizes the execution flow.
*   **Data**: Consumes `StepSnapshot[]` from `runStore`.
*   **Features**:
    *   Displays Node Label, Duration, and **Token Usage**.
    *   Visual indicators for status (Success, Error).

### `TraceInspector.tsx`
*   **Purpose**: Inspects the internal state of a node execution.
*   **Features**:
    *   **State Snapshot**: Full JSON view of `GraphState`.
    *   **Raw Frame**: Debug view of the raw event data.

### `PromptPlayground.tsx`
*   **Purpose**: "Isolated Run" capability. Allows verifying a specific node with modified inputs without running the full graph.
*   **Logic**:
    1.  Uses `useIsolatedRuntime` hook.
    2.  Requires `graphDefinition` (persisted in `RunStore`).
    3.  Sends a targeted execution request to the backend.

## 3. State Management

### `RunStore` (`runStore.ts`)
EXTENDED to support Observability:
*   `tokenUsage`: Consolidated token metrics per node.
*   `pendingStepTokens`: Transient token accumulator for per-step precision.
*   `nodeSnapshots`: History of state changes per node.
*   `graphDefinition`: Persisted copy of the compiled graph for replay/isolation.

### `RuntimeContext` (`RuntimeContext.tsx`)
ABSTRACTION LAYER over the WebSocket:
*   Connects to `/api/ws/run/{graphId}`.
*   Dispatches WebSocket events to `RunStore`.
*   **Events Handled**:
    *   `token_usage`: Updates token counters.
    *   `node_finished`: Captures snapshots (`addSnapshot`).
    *   `interrupt`: Handles HITL breakpoints.
