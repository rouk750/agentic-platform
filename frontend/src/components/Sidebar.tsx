import { Bot, Wrench, GitFork, Settings, Database, Sparkles, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Sidebar() {

    const onDragStart = (event: React.DragEvent, nodeType: string, data?: any) => {
        event.dataTransfer.setData('application/reactflow', nodeType);
        if (data) {
            event.dataTransfer.setData('application/reactflow/data', JSON.stringify(data));
        }
        event.dataTransfer.effectAllowed = 'move';
    };

    return (
        <aside className="w-64 h-full bg-white border-r border-slate-200 p-4 flex flex-col gap-4 z-20 shadow-sm flex-shrink-0">
            <h2 className="font-bold text-slate-800 text-lg">Bibliothèque</h2>

            <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Agents</div>
                <div
                    className="flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-blue-500 hover:text-blue-600 hover:shadow-sm transition-all"
                    onDragStart={(event) => onDragStart(event, 'agent')}
                    draggable
                >
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                        <Bot size={20} />
                    </div>
                    <span className="font-medium">AI Agent</span>
                </div>

                <div
                    className="flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-amber-500 hover:text-amber-600 hover:shadow-sm transition-all"
                    onDragStart={(event) => onDragStart(event, 'smart_node')}
                    draggable
                >
                    <div className="p-2 bg-amber-100 text-amber-600 rounded-lg">
                        <Sparkles size={20} />
                    </div>
                    <div className="flex flex-col">
                        <span className="font-medium">Smart Node</span>
                        <span className="text-[10px] text-amber-600 font-bold uppercase tracking-wider bg-amber-50 px-1 rounded w-fit">Beta</span>
                    </div>
                </div>
            </div>

            <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Nodes</div>

                <div
                    className="flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-purple-500 hover:text-purple-600 hover:shadow-sm transition-all"
                    onDragStart={(event) => onDragStart(event, 'tool')}
                    draggable
                >
                    <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                        <Wrench size={20} />
                    </div>
                    <span className="font-medium">Tool Executor</span>
                </div>

                <div
                    className="flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-purple-500 hover:text-purple-600 hover:shadow-sm transition-all"
                    onDragStart={(event) => onDragStart(event, 'rag', { label: 'RAG Retriever' })}
                    draggable
                >
                    <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                        <Database size={20} />
                    </div>
                    <span className="font-medium">RAG</span>
                </div>

                <div
                    className="flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-purple-500 hover:text-purple-600 hover:shadow-sm transition-all"
                    onDragStart={(event) => onDragStart(event, 'router', { label: 'Logic Router' })}
                    draggable
                >
                    <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                        <GitFork size={20} />
                    </div>
                    <span className="font-medium">Router</span>
                </div>

                <div
                    className="flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-orange-500 hover:text-orange-600 hover:shadow-sm transition-all"
                    onDragStart={(event) => onDragStart(event, 'iterator', { label: 'Loop Iterator' })}
                    draggable
                >
                    <div className="p-2 bg-orange-100 text-orange-600 rounded-lg">
                        <RefreshCw size={20} />
                    </div>
                    <span className="font-medium">Iterator</span>
                </div>
            </div>


        </aside>
    );
}
