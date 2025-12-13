import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, LayoutGrid, Box, Palette, Info } from 'lucide-react';
import { ModelList } from '../features/settings/ModelList';
import { AddModelDialog } from '../features/settings/AddModelDialog';
import { getModels, deleteModel } from '../api/settings';
import type { LLMProfile } from '../types/settings';
import { toast } from 'sonner';


export default function SettingsPage() {
    const [models, setModels] = useState<LLMProfile[]>([]);
    const { section } = useParams();
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [loading, setLoading] = useState(true);

    // Default to 'models' if no section provided (though routing should handle this)
    const activeSection = section || 'models';

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
        if (activeSection === 'models') {
            fetchModels();
        }
    }, [activeSection]);

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
                    <div className="space-y-6">
                        <div>
                            <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">General Settings</h2>
                            <p className="text-sm text-zinc-500 dark:text-zinc-400">Manage global application settings.</p>
                        </div>
                        <div className="text-zinc-500 p-8 text-center border border-dashed rounded-lg bg-zinc-50">
                            General settings coming soon.
                        </div>
                    </div>
                );
            case 'appearance':
                return (
                    <div className="space-y-6">
                        <div>
                            <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">Appearance</h2>
                            <p className="text-sm text-zinc-500 dark:text-zinc-400">Customize the look and feel.</p>
                        </div>
                        <div className="text-zinc-500 p-8 text-center border border-dashed rounded-lg bg-zinc-50">
                            Appearance settings coming soon.
                        </div>
                    </div>
                );
            case 'about':
            case 'help':
                return (
                    <div className="space-y-6">
                        <div>
                            <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">{activeSection.charAt(0).toUpperCase() + activeSection.slice(1)}</h2>
                        </div>
                        <div className="text-zinc-500 p-8 text-center border border-dashed rounded-lg bg-zinc-50">
                            Content for {activeSection} coming soon.
                        </div>
                    </div>
                );
            default:
                return (
                    <div className="text-zinc-500 p-8 text-center border border-dashed rounded-lg">
                        Section not found.
                    </div>
                );
        }
    };

    return (
        <div className="h-full bg-slate-50 p-8">
            <div className="max-w-4xl mx-auto">
                {renderContent()}
            </div>
        </div>
    );
}
