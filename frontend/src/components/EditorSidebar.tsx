import { Bot, Wrench, GitFork, Settings, Database, Sparkles, RefreshCw, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { templateApi, AgentTemplate } from '../api/templates';
import { toast } from 'sonner';

export default function EditorSidebar() {
    const [templates, setTemplates] = useState<AgentTemplate[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadTemplates = async () => {
            try {
                // Ensure backend is reachable and endpoint exists. 
                // Since I just added it, it might fail if backend didn't reload or migrate.
                // But assuming it works:
                const data = await templateApi.getAll();
                setTemplates(data);
            } catch (error) {
                console.error("Failed to load templates", error);
                // Silent error or small toast? Let's just log for sidebar to avoid annoyance
            } finally {
                setLoading(false);
            }
        };
        loadTemplates();
    }, []);

    const onDragStart = (event: React.DragEvent, nodeType: string, data?: any) => {
        event.dataTransfer.setData('application/reactflow', nodeType);
        if (data) {
            event.dataTransfer.setData('application/reactflow/data', JSON.stringify(data));
        }
        event.dataTransfer.effectAllowed = 'move';
    };

    const getTemplateIcon = (type: string) => {
        switch (type) {
            case 'agent': return <Bot size={20} />;
            case 'smart_node': return <Sparkles size={20} />;
            default: return <Bot size={20} />;
        }
    };

    const getTemplateColor = (type: string) => {
        switch (type) {
            case 'agent': return 'blue';
            case 'smart_node': return 'amber';
            default: return 'slate';
        }
    };

    return (
        <aside className="w-64 h-full bg-white border-r border-slate-200 p-4 flex flex-col gap-4 z-20 shadow-sm flex-shrink-0 overflow-y-auto">
            <h2 className="font-bold text-slate-800 text-lg">Bibliothèque</h2>

            {/* My Templates Section */}
            <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex justify-between items-center">
                    My Agents
                    {loading && <Loader2 size={12} className="animate-spin" />}
                </div>

                {!loading && templates.length === 0 && (
                    <div className="text-xs text-slate-400 italic px-1">
                        No saved templates.
                    </div>
                )}

                {templates.map((template) => {
                    let parsedConfig = {};
                    try {
                        parsedConfig = JSON.parse(template.config);
                    } catch (e) { console.error("Bad config", e) }

                    // Merge template name as label if not present, and add templateId ref
                    const dragData = {
                        label: template.name,
                        ...parsedConfig,
                        _templateId: template.id // Store reference
                    };

                    const color = getTemplateColor(template.type);

                    return (
                        <div
                            key={template.id}
                            className={`flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-${color}-500 hover:text-${color}-600 hover:shadow-sm transition-all`}
                            onDragStart={(event) => onDragStart(event, template.type, dragData)}
                            draggable
                        >
                            <div className={`p-2 bg-${color}-100 text-${color}-600 rounded-lg`}>
                                {getTemplateIcon(template.type)}
                            </div>
                            <div className="flex flex-col overflow-hidden">
                                <span className="font-medium truncate" title={template.name}>{template.name}</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="h-px bg-slate-100 my-2"></div>

            <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Base Nodes</div>
                <div
                    className="flex items-center gap-3 p-3 text-slate-700 bg-white border border-slate-200 rounded-lg cursor-grab hover:border-blue-500 hover:text-blue-600 hover:shadow-sm transition-all"
                    onDragStart={(event) => onDragStart(event, 'agent')}
                    draggable
                >
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                        <Bot size={20} />
                    </div>
                    <span className="font-medium">Blank Agent</span>
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
                        <span className="font-medium">Blank Smart Node</span>
                    </div>
                </div>
            </div>

            <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tools</div>

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
