# Frontend Types Technical Specification

## Overview
This directory (`frontend/src/types`) serves as the central dictionary for TypeScript interfaces, ensuring type safety across Store, Components, and API.

## 1. Node Data Structures

### `AgentNodeData` (`agent.ts`)
The payload for Agent Nodes.
*   **Core**: `modelName`, `system_prompt`, `tools`.
*   **Flow Attributes**: `isStart` (Entry point flag).
*   **Template Sync**: `_templateId`, `_templateVersion` (for "Eject" or Update logic).
*   **Model Config**: `profile_id`, `provider`, `model_id` (Flattened for easier access by Backend?).

### `RouterNodeData` (`router.ts`)
*   `routes`: Array of `{ condition, value, target_handle }`.

## 2. Execution Domain (`execution.ts`)

### `Message`
The atomic unit of the Chat/Run log.
*   `role`: 'user' | 'ai' | 'tool' | 'trace' | 'system'.
*   `traceDetails`: `{ nodeId, input, count }` (Used for "Trace" debugging messages).
*   `toolDetails`: `{ name, input, output }`.

## 3. Settings (`settings.ts`)
*   `LLMProfile`: Defines a configured Model Provider.

## 4. Refactoring Opportunities
*   **Zod Integration**: These types are purely static. Integrating `zod` schemas here would allow for runtime validation of API responses, ensuring the Frontend doesn't crash on malformed Backend data.
