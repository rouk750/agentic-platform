# Backend Testing Guidelines

This document outlines the standards, structure, and best practices for testing the Agentic Platform backend.

## 1. Directory Structure

Tests are organized by their scope and the component they target. All tests are located in `backend/tests/`.

```
backend/tests/
├── nodes/          # Unit tests for Node classes (e.g., Agent, SmartNode, ToolNode)
├── tools/          # Tests for individual tools (e.g., OCR, CSV, Generic Tools)
├── engine/         # Tests for the execution engine, compiler, and DSPy integration
├── api/            # Integration tests for FastAPI endpoints
├── integration/    # End-to-end integration tests involving multiple components
└── testing.md      # This file
```

## 2. Naming Conventions

*   **Test Files**: Must start with `test_` (e.g., `test_smart_node.py`).
*   **Test Functions**: Must start with `test_` (e.g., `def test_node_response():`).
*   **Test Classes**: Must start with `Test` (e.g., `class TestSmartNode:`).

> **Note**: Avoid using prefixes like `verify_`. Use `test_` to ensure automatic discovery by `pytest`.

## 3. Tools & Frameworks

*   **Test Runner**: `pytest`
*   **Async Support**: `pytest-asyncio`
*   **Mocking**: `unittest.mock` (Standard Library)
*   **LLM Mocking**: We mock `dspy.LM` or specific provider integrations to avoid making real API calls during tests.

## 4. Writing Tests

### 4.1. Unit Tests (Nodes & Tools)

Unit tests should test components in isolation. Mock external dependencies like database connections or LLM APIs.

**Example: Testing an Async Node**

```python
import pytest
from unittest.mock import MagicMock
from app.nodes.my_node import MyNode

@pytest.mark.asyncio
async def test_my_node_execution():
    # 1. Setup
    config = {"key": "value"}
    node = MyNode("node_1", config)
    state = {"input": "test"}

    # 2. Execute
    result = await node.invoke(state)

    # 3. Verify
    assert "output" in result
    assert result["output"] == "expected"
```

### 4.2. Mocking DSPy

When testing components that use DSPy (`SmartNode`, `Agent`), you **MUST NOT** rely on real LLM calls. Always mock the Language Model.

**Important**: Avoid using global `dspy.settings.configure()` in async tests as it can cause `RuntimeError`. Inject the mock directly or patch `get_dspy_lm`.

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_lm():
    lm = MagicMock()
    lm.return_value = ["Mocked LLM Response"] # DSPy expects list of strings
    return lm

@pytest.mark.asyncio
async def test_dspy_component(mock_lm):
    with patch("app.engine.dspy_utils.get_dspy_lm", return_value=mock_lm):
         # Run your test
         pass
```

### 4.3. API Tests

Use `TestClient` from `fastapi.testclient` (or `httpx` for async) to test endpoints.

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
```

## 5. Running Tests

Run all tests from the project root or backend directory:

```bash
# Using poetry
poetry run pytest backend/tests

# Run specific category
poetry run pytest backend/tests/nodes
```
