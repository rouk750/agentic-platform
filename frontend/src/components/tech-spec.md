# Frontend Components Technical Specification

## Overview
This directory (`frontend/src/components`) contains the specific UI features of the application.
> [!NOTE]
> Currently, the structure is flat, with `src/components/Flow/nodes` being an exception. A refactor to `ui/` vs `features/` is recommended.

## 1. Flow Components

### `FlowEditor` (`FlowEditor.tsx`)
The core canvas wrapper around `ReactFlow`.
*   **Props**: None (uses `useParams` for ID).
*   **Adherences**:
    *   **Store**: `useGraphStore` (nodes/edges), `useRunStore` (reset, `activeNodeIds`, `nodeExecutionCounts`).
    *   **API**: `flowApi` (load/save).
    *   **Drag & Drop**: Native HTML5 DnD handling.
*   **Refactoring Opportunity**:
    *   The "Header" with Save/Back buttons is embedded. It should be extracted to `FlowHeader.tsx`.
    *   Dirty state warning logic (`window.onbeforeunload`) helps prevent data loss.

### `EditorSidebar` (`EditorSidebar.tsx`)
The library of draggable nodes.
*   **Props**: None.
*   **Adherences**:
    *   **API**: `templateApi` (fetches reusable agents).
*   **Refactoring Opportunity**:
    *   Hardcoded styling for "Draggable Cards". A generic `<DraggableItem />` component would clean this up.

## 2. Dialogs

### `AgentTemplateDialog` (`AgentTemplateDialog.tsx`)
A massive modal for configuring Agents and Smart Nodes.
*   **Props**: `isOpen`, `onClose`, `onSave`, `initialData`.
*   **Adherences**:
    *   `react-hook-form`: Complex form state.
    *   `api/settings`: Fetches Models.
    *   `api/smartNode`: Fetches Guardrails.
*   **Refactoring Opportunity**:
    *   **Critical**: This file is 550+ lines. It contains distinct sub-forms:
        *   `AgentConfigForm` (System prompt, tools).
        *   `SmartNodeConfigForm` (Goals, Inputs/Outputs).
    *   These should be split into separate components.
    *   Input Array logic (`fields.map(...)`) is repetitive. A generic `<DynamicList />` component is needed.

## 3. Layout

### `AppSidebar` (`AppSidebar.tsx`)
Main navigation.
*   **Adherences**: `react-router-dom` (`NavLink`).

## 4. Global Refactoring Analysis
The inspection reveals a lack of Atomic Design:
*   **Missing `src/components/ui`**: We see raw Tailwind classes (`px-3 py-2 bg-blue-600...`) repeated everywhere for Buttons and Inputs.
*   **Recommendation**:
    1.  Create `src/components/ui/Button.tsx`.
    2.  Create `src/components/ui/Input.tsx`.
    3.  Create `src/components/ui/Dialog.tsx` (Wrapper for the fixed inset overlay).
