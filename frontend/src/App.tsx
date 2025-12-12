import Sidebar from './components/Sidebar';
import FlowEditor from './components/FlowEditor';
import { ChatPanel } from './features/execution/ChatPanel';
import { Toaster } from 'sonner';

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SettingsPage from './pages/SettingsPage';
import DashboardPage from './pages/DashboardPage';

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
                <Route path="/" element={<DashboardPage />} />
                <Route path="/editor/new" element={<EditorLayout />} />
                <Route path="/editor/:id" element={<EditorLayout />} />
                <Route path="/settings" element={<SettingsPage />} />
            </Routes>
            <Toaster position="top-center" richColors />
        </BrowserRouter>
    );
}

export default App;
