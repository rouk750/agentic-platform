# Backend Models Technical Specification

## Overview
This directory (`backend/app/models`) contains the **SQLModel** (SQLAlchemy + Pydantic) definitions used for Database Object Mapping (ORM).

## 1. Flow Models

### `Flow` (`flow.py`)
Represents a visual graph workflow.
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | PK | Auto-incrementing ID. |
| `name` | `str` | - | Human-readable name. |
| `description` | `str` | `None` | Optional details. |
| `is_archived` | `bool` | `False` | Soft deletion flag. |
| `data` | `str` (JSON) | - | The serialized React Flow graph (nodes, edges, viewport). |
| `created_at` | `datetime` | `utcnow` | Timestamp. |
| `updated_at` | `datetime` | `utcnow` | Timestamp. |

### `FlowVersion` (`flow_version.py`)
Snapshot of a flow's data state.
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | PK | Auto-incrementing ID. |
| `flow_id` | `int` | FK | References `flow.id`. |
| `data` | `str` (JSON) | - | Snapshot of `Flow.data`. |
| `created_at` | `datetime` | `utcnow` | Timestamp of version creation. |
| `is_locked` | `bool` | `False` | Prevents deletion if true. |

## 2. Agent Templates

### `AgentTemplate` (`agent_template.py`)
Reusable configuration for nodes (e.g., a "Writer Agent" preset).
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | PK | Auto-incrementing ID. |
| `name` | `str` | - | Template name. |
| `type` | `str` | - | Node type identifier (e.g., "agent", "smart_node"). |
| `config` | `str` (JSON) | - | Configuration payload (system prompt, model ref, etc.). |
| `is_archived` | `bool` | `False` | Soft deletion flag. |

### `AgentTemplateVersion` (`agent_template.py`)
Versioning info for templates.
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | PK | |
| `template_id` | `int` | FK | References `agenttemplate.id`. |
| `config` | `str` (JSON) | - | Snapshot of config. |
| `version_number` | `int` | `None` | Sequential version counter. |
| `is_locked` | `bool` | `False` | Prevents deletion if true. |

## 3. Settings

### `LLMProfile` (`settings.py`)
Configuration for an LLM Provider.
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `int` | PK | |
| `name` | `str` | (index) | Display name. |
| `provider` | `ProviderType` | - | Enum: `openai`, `anthropic`, `ollama`, etc. |
| `model_id` | `str` | - | Tech name (e.g. `gpt-4`). |
| `base_url` | `str` | `None` | Optional override (for local/azure). |
| `api_key_ref` | `str` | `None` | Pointer to system keyring storage (not the actual key). |
| `temperature` | `float` | `0.7` | Generation strictness. |
