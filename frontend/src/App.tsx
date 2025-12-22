import EditorPage from './pages/EditorPage';
import { Toaster } from 'sonner';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import SettingsPage from './pages/SettingsPage';
import FlowsPage from './pages/FlowsPage';
import AgentsPage from './pages/AgentsPage';
import MainLayout from './components/MainLayout';
import DeepObservabilityPage from './features/observability/DeepObservabilityPage';
import { RuntimeProvider } from './context/RuntimeContext';

function App() {
  return (
    <RuntimeProvider>
      <BrowserRouter>
        <Routes>
          {/* Main App Layout Routes */}
          <Route element={<MainLayout />}>
            <Route path="/" element={<Navigate to="/flows" replace />} />
            <Route path="/flows" element={<FlowsPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/settings" element={<Navigate to="/settings/models" replace />} />
            <Route path="/settings/:section" element={<SettingsPage />} />
          </Route>

          {/* Editor Routes (No Main Sidebar) */}
          <Route path="/editor/new" element={<EditorPage />} />
          <Route path="/editor/:id" element={<EditorPage />} />
          <Route path="/debug/:runId" element={<DeepObservabilityPage />} />
        </Routes>
        <Toaster position="top-center" richColors />
      </BrowserRouter>
    </RuntimeProvider>
  );
}

export default App;
