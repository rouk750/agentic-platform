import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { templateApi, AgentTemplate, AgentTemplateVersion } from '../api/templates';
import { Trash2, History, RotateCcw, Loader2, Plus, Archive, ArchiveRestore, Filter, Bot, BrainCircuit, Pencil } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import AgentTemplateDialog from '../components/AgentTemplateDialog';

type FilterStatus = 'active' | 'archived' | 'all';
type SortOption = 'updated_desc' | 'updated_asc' | 'name_asc';

export default function AgentsPage() {
    // const navigate = useNavigate(); // Navigation logic for editing agents might be different (modal vs page)
    const [templates, setTemplates] = useState<AgentTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
    const [versions, setVersions] = useState<AgentTemplateVersion[]>([]);
    const [loadingVersions, setLoadingVersions] = useState(false);

    // Dialog State
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingTemplate, setEditingTemplate] = useState<AgentTemplate | null>(null);

    // Filters and Sort state
    const [filterStatus, setFilterStatus] = useState<FilterStatus>('active');
    const [sortBy, setSortBy] = useState<SortOption>('updated_desc');

    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        try {
            setLoading(true);
            const data = await templateApi.getAll();
            setTemplates(data);
        } catch (error) {
            console.error("Failed to load templates", error);
            toast.error("Failed to load templates");
        } finally {
            setLoading(false);
        }
    };

    const handleOpenCreate = () => {
        setEditingTemplate(null);
        setIsDialogOpen(true);
    };

    const handleOpenEdit = (template: AgentTemplate) => {
        setEditingTemplate(template);
        setIsDialogOpen(true);
    };

    const handleSaveTemplate = async (templateData: Partial<AgentTemplate>) => {
        try {
            if (editingTemplate) {
                // Update
                const updated = await templateApi.update(editingTemplate.id!, templateData);
                setTemplates(templates.map(t => t.id === updated.id ? updated : t));

                // Refresh versions if this template's history is open
                if (selectedTemplateId === updated.id) {
                    const newVersions = await templateApi.getVersions(updated.id!);
                    setVersions(newVersions);
                }

                toast.success("Template updated successfully");
            } else {
                // Create
                const created = await templateApi.create(templateData as AgentTemplate);
                setTemplates([created, ...templates]);
                toast.success("Template created successfully");
            }
            setIsDialogOpen(false);
        } catch (error) {
            console.error("Failed to save template", error);
            toast.error("Failed to save template");
            throw error; // Re-throw for dialog to handle loading state if needed
        }
    };

    const handleDeleteTemplate = async (id: number) => {
        if (!confirm("Are you sure you want to delete this template? This action cannot be undone.")) return;
        try {
            await templateApi.delete(id);
            setTemplates(templates.filter(t => t.id !== id));
            toast.success("Template deleted");
            if (selectedTemplateId === id) {
                setSelectedTemplateId(null);
                setVersions([]);
            }
        } catch (error) {
            console.error("Failed to delete template", error);
            toast.error("Failed to delete template");
        }
    };

    const handleToggleArchive = async (template: AgentTemplate) => {
        try {
            await templateApi.update(template.id!, { is_archived: !template.is_archived });
            setTemplates(templates.map(t => t.id === template.id ? { ...t, is_archived: !t.is_archived } : t));
            toast.success(template.is_archived ? "Template unarchived" : "Template archived");
        } catch (error) {
            console.error("Failed to update status", error);
            toast.error("Failed to update status");
        }
    };

    const handleViewVersions = async (templateId: number) => {
        if (selectedTemplateId === templateId) {
            setSelectedTemplateId(null);
            setVersions([]);
            return;
        }

        try {
            setSelectedTemplateId(templateId);
            setLoadingVersions(true);
            const data = await templateApi.getVersions(templateId);
            setVersions(data);
        } catch (error) {
            console.error("Failed to load versions", error);
            toast.error("Failed to load versions");
        } finally {
            setLoadingVersions(false);
        }
    };

    const handleRestoreVersion = async (templateId: number, versionId: number) => {
        if (!confirm("Are you sure you want to restore this version?")) return;
        try {
            const restored = await templateApi.restoreVersion(templateId, versionId);
            toast.success("Version restored successfully");
            setTemplates(templates.map(t => t.id === templateId ? restored : t));
        } catch (error) {
            console.error("Failed to restore version", error);
            toast.error("Failed to restore version");
        }
    };

    const handleDeleteVersion = async (templateId: number, versionId: number) => {
        if (!confirm("Are you sure you want to delete this version?")) return;
        try {
            await templateApi.deleteVersion(templateId, versionId);
            toast.success("Version deleted");
            setVersions(versions.filter(v => v.id !== versionId));
        } catch (error) {
            console.error("Failed to delete version", error);
            toast.error("Failed to delete version");
        }
    };

    // Filter and Sort Logic
    const filteredTemplates = templates
        .filter(t => {
            if (filterStatus === 'all') return true;
            if (filterStatus === 'active') return !t.is_archived;
            if (filterStatus === 'archived') return t.is_archived;
            return true;
        })
        .sort((a, b) => {
            if (sortBy === 'name_asc') return a.name.localeCompare(b.name);
            const dateA = new Date(a.updated_at || 0).getTime();
            const dateB = new Date(b.updated_at || 0).getTime();
            return sortBy === 'updated_desc' ? dateB - dateA : dateA - dateB;
        });

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-5xl mx-auto space-y-8">
                {/* Header and Toolbar */}
                <div className="flex flex-col gap-6">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-slate-800">Agent Templates</h1>
                            <p className="text-slate-500">Manage your reusable agents and smart nodes</p>
                        </div>
                        <button
                            onClick={handleOpenCreate}
                            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm font-medium"
                        >
                            <Plus size={18} /> New Template
                        </button>
                    </div>

                    <div className="flex items-center justify-between bg-white p-2 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
                            {(['active', 'archived', 'all'] as const).map((status) => (
                                <button
                                    key={status}
                                    onClick={() => setFilterStatus(status)}
                                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors capitalize ${filterStatus === status ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                                >
                                    {status}
                                </button>
                            ))}
                        </div>

                        <div className="flex items-center gap-2 px-2">
                            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Sort by</span>
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value as SortOption)}
                                className="bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 outline-none"
                            >
                                <option value="updated_desc">Last Updated (Newest)</option>
                                <option value="updated_asc">Last Updated (Oldest)</option>
                                <option value="name_asc">Name (A-Z)</option>
                            </select>
                        </div>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center py-12">
                        <Loader2 className="animate-spin text-blue-600" size={32} />
                    </div>
                ) : filteredTemplates.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-xl border border-slate-200 shadow-sm">
                        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 mb-4">
                            <Filter className="text-slate-400" size={24} />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900 mb-1">No templates found</h3>
                        <p className="text-slate-500 mb-4">You haven't created any templates yet.</p>
                        <button
                            onClick={handleOpenCreate}
                            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg transition-colors font-medium text-sm"
                        >
                            Create your first template
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {filteredTemplates.map((template) => (
                            <div key={template.id} className={`bg-white rounded-xl border-l-[4px] border border-slate-200 shadow-sm overflow-hidden transition-all hover:shadow-md ${template.is_archived ? 'border-l-slate-400 bg-slate-50/50' : template.type === 'agent' ? 'border-l-indigo-500' : 'border-l-amber-500'}`}>
                                <div className="p-4 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${template.is_archived ? 'bg-slate-100 text-slate-500' : template.type === 'agent' ? 'bg-indigo-50 text-indigo-600' : 'bg-amber-50 text-amber-600'}`}>
                                            {template.type === 'agent' ? <Bot size={20} /> : <BrainCircuit size={20} />}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className={`font-semibold ${template.is_archived ? 'text-slate-500 decoration-slate-400' : 'text-slate-800'}`}>{template.name}</h3>
                                                {template.is_archived && <span className="text-[10px] font-bold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded uppercase tracking-wider">Archived</span>}
                                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${template.type === 'agent' ? 'bg-indigo-100 text-indigo-700' : 'bg-amber-100 text-amber-700'}`}>
                                                    {template.type === 'agent' ? 'Agent' : 'Smart Node'}
                                                </span>
                                            </div>
                                            <div className="text-xs text-slate-500 flex gap-3 mt-1">
                                                <span>ID: {template.id}</span>
                                                <span>•</span>
                                                <span>Updated {formatDistanceToNow(new Date(template.updated_at || new Date()), { addSuffix: true })}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => handleToggleArchive(template)}
                                            className="p-2 hover:bg-slate-100 text-slate-500 rounded-lg transition-colors"
                                            title={template.is_archived ? "Unarchive" : "Archive"}
                                        >
                                            {template.is_archived ? <ArchiveRestore size={16} /> : <Archive size={16} />}
                                        </button>
                                        <button
                                            onClick={() => handleViewVersions(template.id!)}
                                            className={`p-2 rounded-lg transition-colors flex items-center gap-1.5 text-sm font-medium ${selectedTemplateId === template.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-50 text-slate-600'}`}
                                        >
                                            <History size={16} />
                                            {selectedTemplateId === template.id ? 'Hide History' : 'History'}
                                        </button>
                                        <button
                                            onClick={() => handleOpenEdit(template)}
                                            className="p-2 hover:bg-slate-50 text-slate-600 rounded-lg transition-colors"
                                            title="Edit"
                                        >
                                            <Pencil size={16} />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteTemplate(template.id!)}
                                            className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>

                                {/* Versions List - Expandable */}
                                {selectedTemplateId === template.id && (
                                    <div className="bg-slate-50 border-t border-slate-200 p-4 animate-in slide-in-from-top-2 duration-200">
                                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 pl-1">Version History</h4>
                                        {loadingVersions ? (
                                            <div className="flex items-center gap-2 text-slate-500 text-sm pl-1"><Loader2 className="animate-spin" size={14} /> Loading...</div>
                                        ) : versions.length === 0 ? (
                                            <p className="text-sm text-slate-500 pl-1">No history available.</p>
                                        ) : (
                                            <div className="space-y-2">
                                                {versions.map((version) => {
                                                    const isActive = template.config === version.config;
                                                    return (
                                                        <div key={version.id} className={`flex items-center justify-between bg-white p-3 rounded-lg border text-sm ${isActive ? 'border-green-200 bg-green-50/30' : 'border-slate-200'}`}>
                                                            <div className="flex items-center gap-3">
                                                                <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${isActive ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>v{version.version_number || version.id}</span>
                                                                <div className="flex flex-col">
                                                                    <div className="flex items-center gap-2">
                                                                        <span className="font-medium text-slate-700">Saved Version</span>
                                                                        {isActive && <span className="text-[10px] font-bold text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full uppercase tracking-wider">Active</span>}
                                                                    </div>
                                                                    <span className="text-xs text-slate-500">{new Date(version.created_at).toLocaleString()} ({formatDistanceToNow(new Date(version.created_at))} ago)</span>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                {isActive ? (
                                                                    <span className="text-xs text-green-600 font-medium px-3 py-1.5">Current</span>
                                                                ) : (
                                                                    <>
                                                                        <button
                                                                            onClick={() => handleRestoreVersion(template.id!, version.id)}
                                                                            className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-blue-50 text-blue-600 rounded-md transition-colors text-xs font-medium border border-transparent hover:border-blue-100"
                                                                        >
                                                                            <RotateCcw size={14} /> Restore
                                                                        </button>
                                                                        <button
                                                                            onClick={() => handleDeleteVersion(template.id!, version.id)}
                                                                            className="p-1.5 hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-md transition-colors"
                                                                            title="Delete Version"
                                                                        >
                                                                            <Trash2 size={14} />
                                                                        </button>
                                                                    </>
                                                                )}
                                                            </div>
                                                        </div>
                                                    )
                                                })}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <AgentTemplateDialog
                isOpen={isDialogOpen}
                onClose={() => setIsDialogOpen(false)}
                onSave={handleSaveTemplate}
                initialData={editingTemplate}
            />
        </div>
    );
}
