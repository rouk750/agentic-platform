# Backend Repositories Technical Specification

## Overview
Data access layer implementing the Repository pattern. Provides a clean abstraction over SQLModel database operations.

## Architecture
```
Services → Repositories → SQLModel Session → SQLite
```

## Directory Structure
```
repositories/
├── __init__.py              # Package exports
├── base.py                  # Generic BaseRepository
├── flow_repository.py       # Flow + FlowVersion repos
└── llm_profile_repository.py # LLMProfile repo
```

---

## BaseRepository (`base.py`)

Generic CRUD repository with type hints.

```python
class BaseRepository[T](Generic[T]):
    def get_by_id(id: int) -> T | None
    def list_all(skip, limit) -> List[T]
    def create(entity: T) -> T
    def update(entity: T) -> T
    def delete(id: int) -> bool
```

### Usage
```python
class FlowRepository(BaseRepository[Flow]):
    pass  # Inherits CRUD, add custom methods
```

---

## FlowRepository (`flow_repository.py`)

| Method | Description |
|--------|-------------|
| `list_all(skip, limit, include_archived)` | Paginated list with archive filter |
| `search_by_name(query)` | Fuzzy name search |
| `archive(flow_id)` | Soft delete |
| `unarchive(flow_id)` | Restore from archive |

---

## FlowVersionRepository (`flow_repository.py`)

| Method | Description |
|--------|-------------|
| `list_by_flow(flow_id)` | All versions for a flow |
| `get_latest(flow_id)` | Most recent version |

---

## LLMProfileRepository (`llm_profile_repository.py`)

| Method | Description |
|--------|-------------|
| `list_by_provider(provider)` | Filter by provider |
| `get_by_model_id(model_id)` | Find by model identifier |
| `exists(model_id)` | Check if model configured |

---

## Adherences
- **Services**: `FlowService`, `AgentTemplateService` inject repositories
- **Session**: Passed from FastAPI dependency injection
- **Models**: Uses `app.models.*` SQLModel entities
