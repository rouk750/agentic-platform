
import EditorSidebar from '../components/EditorSidebar';
import FlowEditor from '../components/FlowEditor';
import { ChatPanel } from '../features/execution/ChatPanel';

export default function EditorPage() {
    return (
        <div className="flex h-screen w-screen overflow-hidden bg-white text-slate-900">
            <EditorSidebar />
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
