# Agentic Platform - Technical Documentation

## 1. Project Overview

**Agentic Platform** is a desktop application for designing and executing local LLM agents.
- **Frontend**: Electron, React, TypeScript, Vite, TailwindCSS.
- **Backend**: Python, FastAPI, LangChain, DSPy.

## 2. Prerequisites

Ensure you have the following installed:
- **Node.js** (v18+) & **npm**
- **Python** (v3.10+)
- **Poetry** (Python dependency manager)

---

## 3. Development Setup

### Backend (Python)

The backend handles the agent orchestration and AI logic.

1.  **Navigate to backend directory**:
    ```bash
    cd backend
    ```

2.  **Install dependencies**:
    ```bash
    poetry install
    ```

3.  **Start Development Server**:
    ```bash
    poetry run start
    ```
    The API will run at `http://localhost:8000`.

4.  **Run Tests**:
    poetry run pytest
    ```

    **Configuration**:
    *   `LANGGRAPH_RECURSION_LIMIT`: Set max steps for agent loops (default: 50).
        ```bash
        LANGGRAPH_RECURSION_LIMIT=100 poetry run start
        ```

### Frontend (Electron/React)

The frontend provides the visual editor and execution interface.

1.  **Navigate to frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Start Development App**:
    ```bash
    npm run dev
    ```
    This will launch the Electron window and start the Vite dev server.
    *Note: In dev mode, the frontend attempts to spawn the backend automatically if not already running, but running them separately gives better logs.*

4.  **Debug Mode (DevTools)**:
    To force open the Chromium Developer Tools (Console) on startup:
    ```bash
    DEBUG_NAV=true npm run dev
    ```

    To enable detailed logs from the Python backend:
    ```bash
    DEBUG_MODE=true npm run dev
    ```

    You can combine both:
    ```bash
    DEBUG_NAV=true DEBUG_MODE=true npm run dev
    ```

5.  **Linting & Type Checking**:
    *   **Lint**: `npm run lint` (ESLint)
    *   **Type Check**: `npm run type-check` (TypeScript)
    *   **Build Check**: `npm run build` (Runs types + vite build)

---

## 4. Building for Production

To create an installable application (`.dmg` for macOS, `.exe` for Windows), follow these steps strictly in order.

### Step 1: Build the Backend Executable

We compile the Python backend into a standalone executable using PyInstaller.

```bash
cd backend
poetry run pyinstaller backend.spec
```
*This creates a `dist/backend` executable inside the `backend/` folder.*

### Step 2: Build & Package the Application

The Electron builder needs the backend executable from Step 1.

```bash
cd frontend
# 1. Build the React application
npm run build 

# 2. Package the Electron app
npx electron-builder
```

### Platform Specifics

*   **macOS**:
    *   Running `npx electron-builder` on macOS will output a `.dmg` in `frontend/dist/`.
    *   You may need to sign the application to share it with others (Apple Developer Program required).

*   **Windows**:
    *   Running `npx electron-builder` on Windows will output an `.exe` installer (NSIS) in `frontend/dist/`.
    *   Ensure you build on a Windows machine (or VM) to generate the Windows executable properly.

---

## 5. Project Structure

```
agentic-platform/
├── backend/                # Python FastAPI Backend
│   ├── app/                # App Logic
│   ├── tests/              # Pytest Tests
│   ├── backend.spec        # PyInstaller Config
│   └── pyproject.toml      # Poetry Dependencies
│
├── frontend/               # Electron + React Frontend
│   ├── electron/           # Main Process Code
│   ├── src/                # Renderer Process (React, Components, Hooks)
│   ├── package.json        # Node Dependencies
│   └── vite.config.ts      # Vite Config
```

## 6. Feature Highlights

### 👁️ Vision & Multimodal Agents
The platform now supports full vision capabilities for local models (Ollama):
*   **Image Reader**: Reads local images, resizes to HD (1920px), and optimizes as JPEG (Quality 95%) to save tokens.
*   **PDF Analysis**: `extract_pdf_content` tool converts PDF pages to images for Vision models.
*   **Ollama Compatibility**: Automatically converts Base64 `ToolMessage` outputs into proper Multimodal messages to trigger Ollama's Vision Encoder and prevent context explosion.

### 🧠 Hybrid Routing
Support for complex agent architectures:
*   Mix **Standard Tools** (like `read_image`) and **Sub-Agents** (Virtual Tools) in the same graph.
*   The compiler automatically routes named calls to Sub-Agents and falls back to the generic Tool Executor for standard tools.
