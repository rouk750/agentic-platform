import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Settings, ArrowLeft, LayoutGrid, Box, Palette, Info } from 'lucide-react';
import { ModelList } from '../features/settings/ModelList';
import { AddModelDialog } from '../features/settings/AddModelDialog';
import { getModels, deleteModel, LLMProfile } from '../api/settings';
import { toast } from 'sonner';


export default function SettingsPage() {
    const [models, setModels] = useState<LLMProfile[]>([]);
    const navigate = useNavigate();
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [activeSection, setActiveSection] = useState('models');

    const fetchModels = async () => {
        try {
            const data = await getModels();
            setModels(data);
        } catch (error) {
            console.error('Failed to fetch models', error);
            toast.error('Failed to load models');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchModels();
    }, []);

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this model?')) return;
        try {
            await deleteModel(id);
            toast.success('Model deleted');
            fetchModels();
        } catch (error) {
            console.error(error);
            toast.error('Failed to delete model');
        }
    };

    const sections = [
        { id: 'general', label: 'General', icon: Box },
        { id: 'models', label: 'Models & Keys', icon: LayoutGrid },
        { id: 'appearance', label: 'Appearance', icon: Palette },
        { id: 'about', label: 'About', icon: Info },
    ];

    const renderContent = () => {
        switch (activeSection) {
            case 'models':
                return (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">Models & Connectors</h2>
                                <p className="text-sm text-zinc-500 dark:text-zinc-400">Configure your LLM providers and API keys.</p>
                            </div>
                            <button
                                onClick={() => setIsAddOpen(true)}
                                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm"
                            >
                                <Plus size={20} />
                                Add Model
                            </button>
                        </div>

                        {loading ? (
                            <div className="text-center py-12">Loading...</div>
                        ) : (
                            <ModelList models={models} onDelete={handleDelete} />
                        )}

                        <AddModelDialog
                            open={isAddOpen}
                            onOpenChange={setIsAddOpen}
                            onModelAdded={fetchModels}
                        />
                    </div>
                );
            case 'general':
                return (
                    <div className="text-zinc-500 p-8 text-center border border-dashed rounded-lg">
                        General settings coming soon.
                    </div>
                );
            case 'appearance':
                return (
                    <div className="text-zinc-500 p-8 text-center border border-dashed rounded-lg">
                        Appearance settings coming soon.
                    </div>
                );
            default:
                return (
                    <div className="text-zinc-500 p-8 text-center border border-dashed rounded-lg">
                        Section under construction.
                    </div>
                );
        }
    };

    return (
        <div className="h-screen flex flex-col bg-white dark:bg-zinc-950">
            {/* Header */}
            <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 px-8 py-4 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-full transition-colors -ml-2 text-zinc-600 dark:text-zinc-400"
                        title="Back to Home"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg">
                            <Settings className="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
                        </div>
                        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Settings</h1>
                    </div>
                </div>
            </header>

            {/* Main Layout */}
            <div className="flex flex-1 overflow-hidden">
                {/* Sidebar */}
                <aside className="w-64 border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/20 p-4 shrink-0 overflow-y-auto">
                    <nav className="space-y-1">
                        {sections.map((section) => {
                            const Icon = section.icon;
                            const isActive = activeSection === section.id;
                            return (
                                <button
                                    key={section.id}
                                    onClick={() => setActiveSection(section.id)}
                                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive
                                        ? 'bg-blue-600 text-white shadow-sm'
                                        : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-800'
                                        }`}
                                >
                                    <Icon size={18} />
                                    {section.label}
                                </button>
                            );
                        })}
                    </nav>
                </aside>

                {/* Content Area */}
                <main className="flex-1 overflow-y-auto p-8">
                    <div className="max-w-4xl mx-auto">
                        {renderContent()}
                    </div>
                </main>
            </div>
        </div>
    );
}
