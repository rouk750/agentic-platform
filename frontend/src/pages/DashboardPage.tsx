import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Folder, Loader2, ArrowRight } from 'lucide-react';
import { flowApi, type Flow } from '../api/flows';
import { toast } from 'sonner';

export default function DashboardPage() {
    const navigate = useNavigate();
    const [flows, setFlows] = useState<Flow[]>([]);
    const [loading, setLoading] = useState(true);
    const [retryCount, setRetryCount] = useState(0);

    const loadFlows = useCallback(async (retries = 0) => {
        try {
            // Loading is handled by caller or initial state

            const data = await flowApi.getAll();
            setFlows(data);
            setRetryCount(0);
            setLoading(false);
        } catch {
            console.error(`Failed to load flows (Attempt ${retries + 1}/6)`);

            if (retries < 5) {
                setRetryCount(retries + 1);
            } else {
                toast.error("Impossible de se connecter au backend après 5 tentatives.");
                setLoading(false);
                setFlows([]);
            }
        }
    }, []);

    useEffect(() => {
        if (retryCount > 0 && retryCount <= 5) {
            const timer = setTimeout(() => {
                loadFlows(retryCount);
            }, 1000);
            return () => clearTimeout(timer);
        }
    }, [retryCount, loadFlows]);

    useEffect(() => {
        // eslint-disable-next-line
        loadFlows();
    }, [loadFlows]);

    const handleCreateNew = () => {
        navigate('/editor/new');
    };

    const handleOpen = (id: number) => {
        navigate(`/editor/${id}`);
    };

    const handleDelete = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        if (!confirm("Are you sure you want to delete this flow?")) return;

        try {
            setLoading(true);
            await flowApi.delete(id);
            toast.success("Flow deleted");
            loadFlows();
        } catch (error) {
            console.error(error);
            toast.error("Failed to delete flow");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">My Flows</h1>
                        <p className="text-slate-500 mt-1">Manage and organize your AI agent workflows</p>
                    </div>
                    <button
                        onClick={handleCreateNew}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition-colors font-medium"
                    >
                        <Plus size={20} />
                        Create New Flow
                    </button>
                </div>

                {/* Grid */}
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 text-slate-500">
                        <Loader2 className="animate-spin text-blue-600" size={32} />
                        {retryCount > 0 ? (
                            <p>Connecting to backend... Attempt {retryCount}/5</p>
                        ) : (
                            <p>Loading flows...</p>
                        )}
                    </div>
                ) : flows.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-xl border border-dashed border-slate-300">
                        <div className="inline-flex p-4 bg-slate-100 rounded-full mb-4 text-slate-400">
                            <Folder size={32} />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-800">No flows yet</h3>
                        <p className="text-slate-500 mb-6 max-w-sm mx-auto">Create your first agentic workflow to get started.</p>
                        <button
                            onClick={handleCreateNew}
                            className="text-blue-600 font-medium hover:underline"
                        >
                            Start a new project
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {/* New Card (Quick Access) */}
                        <div
                            onClick={handleCreateNew}
                            className="bg-white border-2 border-dashed border-slate-200 rounded-xl p-6 flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-all min-h-[200px] group"
                        >
                            <div className="p-3 bg-blue-50 text-blue-500 rounded-full group-hover:scale-110 transition-transform">
                                <Plus size={24} />
                            </div>
                            <span className="font-semibold text-slate-600 group-hover:text-blue-600">New Empty Flow</span>
                        </div>

                        {flows.map(flow => (
                            <div
                                key={flow.id}
                                onClick={() => handleOpen(flow.id!)}
                                className="bg-white border border-slate-200 rounded-xl p-6 cursor-pointer hover:shadow-lg hover:border-blue-300 transition-all group relative overflow-hidden"
                            >
                                <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={(e) => handleDelete(e, flow.id!)}
                                        className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>

                                <div className="mb-4">
                                    <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center text-blue-600 mb-4">
                                        <Folder size={24} />
                                    </div>
                                    <h3 className="font-bold text-lg text-slate-800 mb-1 group-hover:text-blue-600 transition-colors line-clamp-1">{flow.name}</h3>
                                    <p className="text-sm text-slate-500 line-clamp-2 h-10">
                                        {flow.description || "No description"}
                                    </p>
                                </div>

                                <div className="flex justify-between items-center text-xs text-slate-400 border-t border-slate-100 pt-4">
                                    <span>Updated {new Date(flow.updated_at!).toLocaleDateString()}</span>
                                    <div className="flex items-center gap-1 text-blue-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity -translate-x-2 group-hover:translate-x-0">
                                        Open <ArrowRight size={12} />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
