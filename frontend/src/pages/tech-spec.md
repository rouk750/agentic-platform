# Frontend Pages Technical Specification

## Overview
This directory (`frontend/src/pages`) contains top-level route components managed by `react-router-dom`.
> [!NOTE]
> The **Flow Editor** is NOT a page component here. It is handled by `EditorLayout` in `App.tsx`, composing `EditorSidebar`, `FlowEditor`, and `ChatPanel`.

## 1. Management Pages

### `FlowsPage` (`FlowsPage.tsx`)
A dashboard to list, sort, filter, and manage Flows.
*   **Adherences**:
    *   **Hooks**: `useApiResource` (CRUD), `useSortAndFilter`, `useVersionHistory`.
    *   **Hooks**: `useApiResource` (CRUD), `useSortAndFilter`, `useVersionHistory`.
    *   **API**: `flowApi`.
    *   **Features**: Version Locking, Bulk Version Delete, Restore-in-place.
    *   **Route**: `/flows`.

### `AgentsPage` (`AgentsPage.tsx`)
A library view for Agent Templates ("Blueprints").
*   **Adherences**:
    *   **Hooks**: `useApiResource`, `useVersionHistory`.
    *   **API**: `templateApi`.
    *   **Dialog**: `AgentTemplateDialog` for creating/editing.
    *   **Features**: Version Locking, Bulk Version Delete, Restore-in-place.
    *   **Route**: `/agents`.

### `SettingsPage` (`SettingsPage.tsx`)
Application configuration (mainly LLM Models).
*   **Adherences**:
    *   **Components**: `ModelList`, `AddModelDialog`.
    *   **API**: `getModels`, `deleteModel`, `testSavedModel` (Direct API module usage, legacy pattern?).
    *   **Route**: `/settings/:section` (models, general, appearance).

## 2. Dashboard

### `DashboardPage` (`DashboardPage.tsx`)
(Likely an overview with stats, currently less critical).

## 3. Architecture Note
The application uses a **Layout-based** routing strategy:
*   `MainLayout`: Sidebar + Page Content (Flows, Agents, Settings).
*   `EditorLayout` (in `App.tsx`): Fullscreen editor Mode.
