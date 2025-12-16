# Frontend API Technical Specification

## Overview
This directory (`frontend/src/api`) contains the Axios wrappers for the Backend REST API. These functions are the strict boundary between Frontend and Backend.

## 1. Flow API (`flows.ts`)
Manages `Flow` entities (the graphs).

### Function Reference
| Function | Signature | Description |
|---|---|---|
| `getAll` | `() => Promise<Flow[]>` | Fetches all flows. |
| `getOne` | `(id: number) => Promise<Flow>` | Fetches single flow by ID. |
| `create` | `(flow: Flow) => Promise<Flow>` | Creates new flow. |
| `update` | `(id: number, flow: Partial<Flow>) => Promise<Flow>` | Updates flow (and triggers versioning if data changed). |
| `getVersions` | `(id: number) => Promise<any[]>` | Fetches history. |
| `restoreVersion` | `(fid: number, vid: number) => Promise<Flow>` | Reverts flow to version. |

### Adherences & Usage
*   **Dependencies**: `axios`, `window.electronAPI` (for port discovery).
*   **Consumed By**:
    *   `src/hooks/useApiResource.ts` (Generic CRUD wrapper).
    *   `src/pages/FlowsPage.tsx` (Direct calls or via hook).
    *   `src/store/graphStore.ts` (Loading graphs into editor).

## 2. Settings API (`settings.ts`)
Manages `LLMProfile` configurations.

### Function Reference
| Function | Signature | Description |
|---|---|---|
| `getModels` | `() => Promise<LLMProfile[]>` | List all profiles. |
| `createModel` | `(p: LLMProfileCreate) => Promise<LLMProfile>` | Save new profile. |
| `testSavedModel` | `(id: number) => Promise<boolean>` | Test connection for existing profile. |
| `scanOllamaModels` | `() => Promise<string[]>` | Auto-discover local Ollama tags. |
| `testConnection` | `(provider, model, key, url) => Promise<boolean>` | Test transient connection params. |

### Adherences & Usage
*   **Dependencies**: `axios`, `types/settings`.
*   **Consumed By**:
    *   `src/components/settings/ModelList.tsx` (Listing & Testing).
    *   `src/components/settings/AddModelDialog.tsx` (Creation & Scanning).
    *   `src/components/nodes/AgentConfigDialog.tsx` (Fetching models for dropdown).

## 3. Smart Node API (`smartNode.ts`)
Interacts with DSPy optimization services.

### Function Reference
| Function | Signature | Description |
|---|---|---|
| `getAvailableGuardrails` | `() => Promise<GuardrailDefinition[]>` | Lists validators (Regex, JSON). |
| `optimizeNode` | `(payload: OptimizationPayload) => Promise<any>` | Triggers DSPy compilation. |

### Adherences & Usage
*   **Consumed By**:
    *   `src/components/nodes/SmartNodeConfigDialog.tsx` (Configuration UI).

## 4. Templates API (`templates.ts`)
Manages `AgentTemplate` (presets).

### Function Reference
*   `getAll`, `getOne`, `create`, `update`, `delete`.
*   `getVersions`, `restoreVersion`, `deleteVersion`.

### Adherences & Usage
*   **Consumed By**:
    *   `src/hooks/useApiResource.ts`.
    *   `src/pages/AgentsPage.tsx`.
