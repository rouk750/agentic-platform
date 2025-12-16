# Backend Schemas Technical Specification

## Overview
This directory (`backend/app/schemas`) contains **Pydantic** models (DTOs) for API validation and serialization.

## 1. Flow Schemas (`flow.py`)

### `FlowCreate`
Payload for `POST /api/flows`.
*   `name` (str)
*   `description` (Optional[str])
*   `data` (str): JSON string of graph.

### `FlowRead`
Response model.
*   Inherits `FlowCreate`.
*   Adds `id`, `created_at`, `updated_at`, `is_archived`.

## 2. Settings Schemas (`settings.py`)

### `LLMProfileCreate`
Payload for `POST /api/settings/models`.
*   `name`, `provider` (str).
*   `model_id` (str): e.g. "gpt-4".
*   `base_url` (Optional[str]).
*   `api_key` (Optional[str]): **Sensitive**. Handled securely in router.

## 3. Agent Templates (`agent_template.py`)

### `AgentTemplateCreate`
*   `name`, `description`, `type`.
*   `config` (str): JSON configuration.

## 4. DSPy Interaction (`dspy_schema.py`)

### `OptimizationRequest`
Payload for `POST /api/smart-nodes/optimize`.
*   `node_id` (str)
*   `goal` (str): Improvement objective.
*   `mode` (str): "Predict" vs "ChainOfThought".
*   `inputs` / `outputs`: List of field definitions.
*   `examples`: List of `DSPyExample` (input/output pairs).
*   `metric` (str): "semantic" or "exact_match".
*   `max_rounds` (int).

### `OptimizationResponse`
*   `status` (str)
*   `compiled_program_path` (str)
*   `score` (float)
