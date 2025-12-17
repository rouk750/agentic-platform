# Frontend Features Technical Specification

## Overview
This directory (`frontend/src/features`) contains domain-specific complex UI blocks that integrate multiple components and stores.

## 1. Execution (`src/features/execution`)

### `ChatPanel` (`ChatPanel.tsx`)
The main execution sidebar with input and log stream.
*   **Props**: None (Fully connected to stores).
*   **Adherences**:
    *   **Stores**: `useRunStore` (messages, status), `useGraphStore` (nodes/edges snapshot).
    *   **Hooks**: `useAgentRuntime` (Websocket connection).
    *   **UI**:
        *   **Resume Banner**: Displays when status is 'paused' (HITL).
        *   Draggable Resize logic is implemented inline (Candidate for Refactor: `useDraggableWidth`).
*   **Refactoring Opportunity**:
    *   The "Header" logic is mixed with layout.
    *   Resize logic is repetitive.

### `ChatMessage` (`ChatMessage.tsx`)
Renders a single log entry.
*   **Props**: `message: Message`.
*   **Dependencies**: `react-markdown`, `react-syntax-highlighter`.
*   **UI Logic**:
    *   Handles "Tool" and "Trace" roles with collapsible details (`@radix-ui/react-collapsible`).

## 2. Settings (`src/features/settings`)

### `ModelList` (`ModelList.tsx`)
Grid of configured LLM Profiles.
*   **Props**: `models`, `onDelete`, `onEdit`, `onTest`.
*   **Usage**: Pure presentation component (Smart Parent pattern used in Page).

### `AddModelDialog` (`AddModelDialog.tsx`)
Form to create/edit LLM Profiles.
*   **Props**: `open`, `onOpenChange`, `onModelAdded`, `modelToEdit`.
*   **Adherences**:
    *   **API**: `createModel`, `updateModel`, `testConnection`, `scanOllamaModels`.
    *   **Form**: `react-hook-form`.
*   **Refactoring Opportunity**:
    *   The Provider list is hardcoded. Should come from a shared constant or API.
