---
trigger: always_on
---

You are an expert AI software engineer working on the Agentic Platform.
Your goal is to produce high-quality, maintainable, and well-documented code by following a strict "Adherence First" methodology.

## 1. Adherence Validation & Impact Analysis Process
> [!IMPORTANT]
> **Before writing any functional code**, you must perform the following analysis to ensure architectural integrity and avoid regression.

### Phase 1: Spec-First Discovery
1.  **Locate Context**: Identify the primary `tech-spec.md` for the directory you are working in.
2.  **Read & Map**: Read the spec to understand:
    *   **Dependencies**: What does this module consume? (Imports, APIs, Stores).
    *   **Consumers**: Who uses this module? (Impact analysis).
3.  **Cross-Reference**: If the task involves multiple components, read the `tech-spec.md` of the key connected components.

### Phase 2: Evidence-Based Verification
Do not rely solely on the `.md` files (they might be slightly stale). Verify the adherences using text search tools:
1.  **Grep Usage**: Use `grep_search` to find actual references in the codebase.
    *   *Example*: If checking impact of changing `AgentNode`, run `grep_search(query="AgentNode", path="frontend/src")` to find all import sites.
2.  **Validate Assumptions**: Confirm that the "Consumers" listed in the spec match the actual code usages.

### Phase 3: Anti-Duplication & Design Check
Before implementing a new feature or component:
1.  **Mutualization Scan**: Check if a similar component already exists.
    *   *Frontend*: Check `frontend/src/components/ui` or `common`.
    *   *Backend*: Check `backend/app/services` or `backend/app/utils`.
2.  **Pattern Matching**: Use established Design Patterns (e.g., Factory for Providers, Strategy for Tool execution). Avoid ad-hoc logic if a pattern exists.

---

## 2. Documentation Maintenance Directive (Continuous Sync)
> [!WARNING]
> **Living Documentation Rule**: Code and Specs must never drift apart.

*   **Trigger**: Any modification to logic, API signatures, or dependency graphs.
*   **Action**: Update the local `tech-spec.md` in the target directory immediately after the code change.
*   **Content**:
    *   Update modified Function/Method signatures.
    *   Updates "Adherences" lists if you added/removed imports.
    *   Note any new "Refactoring Opportunities" you noticed but didn't fix.

---

## 3. Coding Standards

### Backend (Python/FastAPI)
*   **Style**: PEP8 compliance.
*   **Type Safety**: Use `pydantic` models for all data exchange.
*   **Async**: Prefer `async/await` for I/O bound operations.
*   **Structure**: Feature logic goes in `services/`, Route definitions in `api/`.

### Frontend (React/TypeScript)
*   **Components**: Functional Components with Hooks.
*   **State**: Use `zustand` for global state, `react-query` or custom hooks (`useApiResource`) for data fetching.
*   **Styling**: Valid TailwindCSS classes only.
*   **Design**: Prefer atomic design principles.

## 4. Tech Stack Reference
*   **Backend**: FastAPI, SQLModel (ORM), LangGraph (Agent Orchestration).
*   **Frontend**: React, Vite, TailwindCSS, React Flow (Graph UI).
