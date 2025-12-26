# Agentic Platform Frontend

The visual interface for the Agentic Platform, built with **React**, **Vite**, **TailwindCSS**, and **React Flow**.

## 🏗 Architecture

High-performance visual editor for AI agents.

- **State Management**: Zustand (global state) + React Query (server state).
- **Graph Editing**: React Flow with custom nodes (`/src/components/nodes`).
- **API Integration**: Centralized `apiClient` with JSON:API support and typed hooks.

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm

### Installation

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run Development Server**:
   ```bash
   npm run dev
   ```
   Access the app at `http://localhost:5173`.

## 🧪 Testing

Tests are centralized in the `tests/` directory (outside `src/`).

### Run All Tests
Using Vitest:
```bash
npm run test
```
*Note: This runs in watch mode by default.*

### Run Single Run
To run tests once without watching:
```bash
npm run test:run
# OR
npm run test -- --run
```

### Run Coverage Analysis
To generate a coverage report:
```bash
npm run coverage
# OR
npm run test -- --run --coverage
```

### Test Structure
- `tests/api/`: API utilities and error handling tests.
- `tests/hooks/`: Custom hooks integration tests (e.g., `useApiResource`).
- `tests/setup.ts`: Test environment configuration.

## 🛠 Key Features

### API Integration (`src/hooks/useApiResource.ts`)
A generic hook for CRUD operations that handles:
- Loading states
- Error parsing (JSON:API & Legacy)
- Toast notifications (Sonner)
- Type-safe responses

### Error Handling (`src/api/errorHandler.ts`)
Unified parser for backend errors, supporting:
- Pydantic validation errors
- JSON:API error objects
- Network failures

## 📚 Documentation

See `docs/` for detailed guides on specific subsystems.
