import Sidebar from './components/Sidebar';
import FlowEditor from './components/FlowEditor';
import { ChatPanel } from './features/execution/ChatPanel';
import { Toaster } from 'sonner';

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import SettingsPage from './pages/SettingsPage';
import DashboardPage from './pages/DashboardPage';
import FlowsPage from './pages/FlowsPage';
import MainLayout from './components/MainLayout';

function EditorLayout() {
    return (
        <div className="flex h-screen w-screen overflow-hidden bg-white text-slate-900">
            <Sidebar />
            <div className="flex-1 h-full relative overflow-auto">
                <div className="flex h-full w-full relative">
                    <div className="flex-1 h-full relative">
                        <FlowEditor />
                    </div>
                    <ChatPanel />
                </div>
            </div>
        </div>
    );
}

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Main App Layout Routes */}
                <Route element={<MainLayout />}>
                    <Route path="/" element={<Navigate to="/flows" replace />} />
                    <Route path="/flows" element={<FlowsPage />} />
                    <Route path="/settings" element={<Navigate to="/settings/models" replace />} />
                    <Route path="/settings/:section" element={<SettingsPage />} />
                </Route>

                {/* Editor Routes (No Main Sidebar) */}
                <Route path="/editor/new" element={<EditorLayout />} />
                <Route path="/editor/:id" element={<EditorLayout />} />
            </Routes>
            <Toaster position="top-center" richColors />
        </BrowserRouter>
    );
}

export default App;
