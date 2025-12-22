# Frontend API Technical Specification

## Overview
API layer containing Axios wrappers for the Backend REST API. Includes JSON:API support and centralized error handling.

## Directory Structure
```
api/
├── apiClient.ts       # Centralized axios client with JSON:API toggle
├── errorHandler.ts    # Unified error parsing (JSON:API, FastAPI, network)
├── flows.ts           # Flow CRUD + versioning
├── templates.ts       # AgentTemplate CRUD + versioning
├── settings.ts        # LLMProfile management
├── smartNode.ts       # DSPy optimization services
└── jsonapi/
    ├── types.ts       # JSON:API TypeScript interfaces
    └── deserializer.ts # Response transformation utilities
```

## API Client (`apiClient.ts`)
Centralized axios instance with:
- **Dynamic base URL** (Electron port discovery)
- **JSON:API content negotiation** via `VITE_USE_JSON_API` flag
- **Response interceptors** for error logging

## Error Handling (`errorHandler.ts`)
| Function | Description |
|----------|-------------|
| `parseApiError` | Extracts user-friendly message from any error type |
| `logError` | Structured error logging for debugging |
| `handleAsync` | Go-style `[result, error]` pattern for promises |

## JSON:API Layer (`jsonapi/`)
### Types (`types.ts`)
- `JSONAPIResource<TAttributes>`, `JSONAPIDocument`
- Domain attributes: `FlowAttributes`, `AgentTemplateAttributes`

### Deserializer (`deserializer.ts`)
| Function | Description |
|----------|-------------|
| `deserializeOne` | Single resource → domain object |
| `deserializeMany` | Collection → `{ items, meta }` |
| `isJsonApiError` | Type guard for error responses |

## Flow API (`flows.ts`)
| Function | Signature |
|----------|-----------|
| `getAll` | `() => Promise<Flow[]>` |
| `create` | `(flow: FlowCreate) => Promise<Flow>` |
| `update` | `(id, flow: FlowUpdate) => Promise<Flow>` |
| `getVersions` | `(id) => Promise<FlowVersion[]>` |
| `restoreVersion` | `(fid, vid) => Promise<Flow>` |
| `toggleLock` | `(fid, vid, isLocked) => Promise<void>` |

## Templates API (`templates.ts`)
Same structure as Flow API but for `AgentTemplate` entities.

## Settings API (`settings.ts`)
| Function | Description |
|----------|-------------|
| `getModels` | List all LLM profiles |
| `createModel` | Create new profile |
| `updateModel` | Update existing profile |
| `deleteModel` | Delete profile |
| `testConnection` | Test LLM connectivity |

## Adherences
- **Hooks**: `useApiResource`, `useVersionHistory` consume these APIs
- **Types**: Re-export domain types from `@/types` for backward compatibility
- **Stores**: `graphStore.ts` uses flow API for loading graphs
