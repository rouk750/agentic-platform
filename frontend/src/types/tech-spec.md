# Frontend Types Technical Specification

## Overview
Central type definitions for the frontend application. All types are exported from `types/index.ts` for clean imports.

## Directory Structure
```
types/
├── index.ts          # Central barrel export
├── flow.ts           # Flow, FlowVersion, FlowCreate, FlowUpdate
├── template.ts       # AgentTemplate, AgentTemplateVersion
├── settings.ts       # LLMProfile, LLMProvider
├── agent.ts          # AgentNodeData
├── router.ts         # RouterNodeData, RouteCondition
├── smartNode.ts      # SmartNodeData
├── iterator.ts       # IteratorNodeData
├── execution.ts      # Message, LogEntry
└── common.ts         # NodeData, SchemaField
```

## Domain Entities

### Flow (`flow.ts`)
| Type | Description |
|------|-------------|
| `Flow` | Workflow graph entity |
| `FlowVersion` | Historical snapshot |
| `FlowCreate` | Creation payload (no id/timestamps) |
| `FlowUpdate` | Partial update payload |

### AgentTemplate (`template.ts`)
| Type | Description |
|------|-------------|
| `AgentTemplate` | Reusable agent configuration |
| `AgentTemplateVersion` | Historical snapshot |

### LLMProfile (`settings.ts`)
| Type | Description |
|------|-------------|
| `LLMProvider` | Union: 'openai' \| 'anthropic' \| etc. |
| `LLMProfile` | Model configuration entity |

## Node Data Types

### `AgentNodeData` (`agent.ts`)
- **Core**: `modelName`, `system_prompt`, `tools`
- **Flow**: `isStart` (entry point flag)
- **Template Sync**: `_templateId`, `_templateVersion`

### `RouterNodeData` (`router.ts`)
- `routes`: Array of `RouteCondition`

## JSON:API Integration
JSON:API attribute types are defined in `api/jsonapi/types.ts`:
- `FlowAttributes`, `AgentTemplateAttributes`, `LLMProfileAttributes`
- Deserializers in `deserializer.ts` convert JSON:API → domain types

## Adherences
- **API Layer**: `api/flows.ts`, `api/templates.ts` re-export domain types
- **Hooks**: `useApiResource`, `useVersionHistory` use domain types
- **Stores**: `runStore.ts` uses `Message`, `LogEntry` from execution

