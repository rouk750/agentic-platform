# Frontend Nodes Technical Specification

## Overview
This directory (`frontend/src/nodes`) contains the specific React Flow node components and their configuration dialogs.

## 1. Agent Logic

### `AgentNode` (`AgentNode.tsx`)
The primary LLM Agent node.
*   **Data Props**: `AgentNodeData` (`system_prompt`, `modelName`, `tools`, `require_approval`, etc.).
*   **Visuals**:
    *   **HITL Badge**: Displays if `require_approval` is true.
    *   **Status Indicators**: Active/Loop Count.
*   **Handles**:
    *   **Target (Left)**: Input.
    *   **Source (Right)**: Output.
    *   **Source (Bottom)**: "Tool Call" (Special edge type?).
*   **Adherences**:
    *   **Dialog**: Opens `AgentConfigDialog`.
    *   **API**: Uses `templateApi.getVersions` for version history.
    *   **Store**: Reads `activeNodeId` from `runStore` for visual highlighting.

### `SmartNode` (`SmartNode.tsx`)
A variant of AgentNode with more structured goals/guardrails (not analyzed in depth but follows similar pattern).

## 2. Control Flow

### `RouterNode` (`RouterNode.tsx`)
Logic branching based on string matching or LLM classification.
*   **Data Props**: `RouterNodeData` (`routes: { condition, value, target_handle }[]`).
*   **Handles**:
    *   **Target (Left)**: Input.
    *   **Source (Dynamic Right)**: One handle per route, plus a "default".
*   **Adherences**: Opens `RouterConfigDialog`.

### `ToolNode` (`ToolNode.tsx`)
A placeholder node representing tool execution context.
*   **UI**: Displays "Executing..." state when `currentToolName` matches.
*   **Handles**:
    *   **Target (Top)**: Input.
    *   **Source (Left)**: Output.
*   **Adherences**: `useRunStore` (checking `currentToolName`).

## 3. Configuration Dialogs
These are large forms triggered by the nodes.
*   `AgentConfigDialog.tsx`: Heavy coupling with `api/settings` and `api/tools`. Includes "Require Approval" (HITL) toggle.
*   `RouterConfigDialog.tsx`: Manages the list of routes.

## 4. Refactoring Opportunities
*   **Node Header**: The header logic (Icon + Title + Actions) is identical across `AgentNode`, `RouterNode`, and `ToolNode`. Extract to `NodeHeader.tsx`.
*   **Dialogs**: `AgentConfigDialog` is too large. Split into tabs/components.
