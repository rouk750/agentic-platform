# Frontend Hooks Technical Specification

## Overview
This directory (`frontend/src/hooks`) contains custom React hooks for reusable logic, API interaction, and runtime management.

## 1. Runtime (`useAgentRuntime.ts`)
Manages the WebSocket connection to the backend execution engine.

### Signature
```typescript
function useAgentRuntime(): {
  connect: (graphJson: any, input: string) => void;
  stop: () => void;
}
```

### Side Effects & Adherences
*   **WebSocket**: Connects to `ws://localhost:8000/api/ws/run/{graphId}`.
*   **Store Updates**: Heavily couples with `runStore` (updating status, logs, tokens).
    *   `setStatus('connecting' | 'running' | 'done')`
    *   `addLog(...)`
    *   `setActiveNode(...)`
*   **Toast**: Triggers `sonner` toasts on error.

## 2. API Resource (`useApiResource.ts`)
A generic CRUD hook to reduce boilerplate in Pages.

### Signature
```typescript
function useApiResource<T, TCreate, TUpdate>(
  options: ApiResourceOptions<T, TCreate, TUpdate>
): {
  items: T[];
  loading: boolean;
  fetchAll: () => Promise<void>;
  create: (data: TCreate) => Promise<T>;
  update: (id: number, data: TUpdate) => Promise<T>;
  remove: (id: number) => Promise<void>;
}
```

### Adherences
*   **Dependencies**: Requires an API object matching the standard interface (`getAll`, `create`, `update`, `delete`).
*   **UI Feedback**: Automatically handles `toast.success` and `toast.error` for all operations.

## 3. Utilities

### `useSortAndFilter` (`useSortAndFilter.ts`)
*   **Description**: Client-side filtering and sorting for lists (e.g., Templates, Flows).
*   **Return**: `{ sortedItems, filter, setFilter, sort, setSort }`.

### `useVersionHistory` (`useVersionHistory.ts`)
*   **Description**: Manages state for "Time Travel" features (Flows/Templates).
*   **Adherences**: Assumes API endpoints for `getVersions` and `restoreVersion`.
