import { Handle, Position, useReactFlow, type NodeProps, type Node } from '@xyflow/react';
import type { AgentNodeData } from '../types/agent';
import { Bot, Settings2, Wrench, FileText, Cpu, Box, Info, History, Loader2, UserCheck } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useState, useEffect } from 'react';
import { useRunStore } from '../store/runStore';
import { AgentConfigDialog } from './AgentConfigDialog';
import { TechnicalInfoDialog } from './TechnicalInfoDialog';
import { templateApi, type AgentTemplateVersion } from '../api/templates';
import { toast } from 'sonner';

type AgentNodeType = Node<AgentNodeData>;

export function AgentNode({ id, data, selected }: NodeProps<AgentNodeType>) {
    const { updateNodeData } = useReactFlow();
    const activeNodeId = useRunStore((state) => state.activeNodeId);
    const isActive = id === activeNodeId;
    const [configOpen, setConfigOpen] = useState(false);
    const [infoOpen, setInfoOpen] = useState(false);

    // Template Versioning State
    const [versions, setVersions] = useState<AgentTemplateVersion[]>([]);
    const [versionsLoading, setVersionsLoading] = useState(false);
    const isTemplate = !!data._templateId;

    const toolCount = data.tools?.length || 0;
    const modelName = data.modelName || "Select Model";
    const hasPrompt = !!data.system_prompt;

    // Fetch versions if this is a template node
    useEffect(() => {
        if (isTemplate && data._templateId) {
            const loadVersions = async () => {
                try {
                    setVersionsLoading(true);
                    const v = await templateApi.getVersions(data._templateId!);
                    // Sort descending by version number
                    setVersions(v.sort((a, b) => b.version_number - a.version_number));
                } catch (e) {
                    console.error("Failed to load versions", e);
                } finally {
                    setVersionsLoading(false);
                }
            };
            loadVersions();
        }
    }, [isTemplate, data._templateId]);

    const handleVersionChange = (versionId: string) => {
        const version = versions.find(v => v.id.toString() === versionId);
        if (!version) return;

        if (confirm(`Apply version ${version.version_number}? This will overwrite current settings.`)) {
            try {
                const config = JSON.parse(version.config);
                // Map config back to node data structure
                // Note: The config structure in DB matches the form data structure
                // We need to ensure we map it correctly to AgentNodeData

                // Common fields
                let updates: Partial<AgentNodeData> = {
                    _templateVersion: version.version_number,
                    system_prompt: config.system_prompt,
                    max_iterations: config.max_iterations,
                    tools: config.tools,
                    output_schema: config.output_schema,
                    flexible_mode: config.flexible_mode,
                };

                // Model fields - we might need to look them up again if full details aren't in config
                // Usually template config saves compact model references or full objects. 
                // Based on AgentTemplateDialog, we save: 
                // { profile_id, modelId, modelName, provider, model_id, ... }
                if (config.profile_id) {
                    updates = {
                        ...updates,
                        profile_id: config.profile_id,
                        modelId: config.modelId,
                        modelName: config.modelName,
                        provider: config.provider,
                        model_id: config.model_id
                    };
                }

                updateNodeData(id, updates);
                toast.success(`Restored version ${version.version_number}`);
            } catch (e) {
                console.error("Failed to apply version", e);
                toast.error("Failed to apply version config");
            }
        }
    };

    return (
        <>
            <div
                className={twMerge(
                    'bg-white border-2 rounded-xl w-64 shadow-sm transition-all duration-300 group',
                    selected ? 'border-primary ring-2 ring-primary/20 shadow-md' : 'border-slate-200 hover:border-slate-300',
                    isActive && 'border-green-500 ring-4 ring-green-500/20 shadow-xl scale-105'
                )}
            >
                {/* Header */}
                <div className="flex items-center gap-3 p-3 border-b border-slate-100 bg-gradient-to-b from-white to-slate-50/50 rounded-t-xl">
                    <div className={twMerge(
                        "p-2 rounded-lg transition-colors flex items-center justify-center relative",
                        isActive ? "bg-green-100 text-green-600" : "bg-blue-100 text-blue-600"
                    )}>
                        <Bot size={18} />
                        {data.isStart && (
                            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white shadow-sm flex items-center justify-center" title="Entry Point">
                                <div className="w-1 h-1 bg-white rounded-full"></div>
                            </div>
                        )}
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                            <input
                                className="font-bold text-slate-800 bg-transparent border-none p-0 focus:ring-0 w-full text-sm truncate placeholder:text-slate-400"
                                value={String(data.label)}
                                onChange={(e) => updateNodeData(id, { label: e.target.value })}
                                placeholder="Agent Name"
                            />
                            {/* Version Selector */}
                            {isTemplate && (
                                <div className="ml-2 flex-shrink-0 relative">
                                    {versionsLoading ? (
                                        <Loader2 size={12} className="animate-spin text-slate-400" />
                                    ) : (
                                        <div className="flex items-center gap-1 bg-slate-100 rounded px-1.5 py-0.5 border border-slate-200">
                                            <History size={10} className="text-slate-500" />
                                            <select
                                                className="bg-transparent text-[10px] font-medium text-slate-600 outline-none border-none p-0 w-auto cursor-pointer appearance-none hover:text-blue-600"
                                                value={data._templateVersion ? versions.find(v => v.version_number === data._templateVersion)?.id || '' : ''}
                                                onChange={(e) => handleVersionChange(e.target.value)}
                                                title="Select Template Version"
                                            >
                                                <option value="" disabled>v{data._templateVersion || '??'}</option>
                                                {versions.map(v => (
                                                    <option key={v.id} value={v.id}>
                                                        v{v.version_number}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1 mt-0.5">
                            <Cpu size={10} />
                            <span className="truncate max-w-[120px]">{modelName}</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-1">
                        <button
                            onClick={() => setInfoOpen(true)}
                            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                            title="Technical Info"
                        >
                            <Info size={16} />
                        </button>
                        <button
                            onClick={() => setConfigOpen(true)}
                            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
                        >
                            <Settings2 size={16} />
                        </button>
                    </div>
                </div>

                {/* Body Summary */}
                <div className="p-3 flex items-center gap-4 text-xs text-slate-500">
                    <div className={twMerge("flex items-center gap-1.5", hasPrompt ? "text-slate-700" : "text-slate-300")}>
                        <FileText size={14} />
                        <span className="font-medium">{hasPrompt ? "Prompt Set" : "No Prompt"}</span>
                    </div>
                    <div className={twMerge("flex items-center gap-1.5", toolCount > 0 ? "text-slate-700" : "text-slate-300")}>
                        <Wrench size={14} />
                        <span className="font-medium">{toolCount} Tool{toolCount !== 1 && 's'}</span>
                    </div>
                    {data.output_schema && data.output_schema.length > 0 && (
                        <div className="flex items-center gap-1.5 text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded border border-purple-100">
                            <Box size={12} />
                            <span className="font-bold text-[10px]">JSON</span>
                        </div>
                    )}
                    {data.require_approval && (
                        <div className="flex items-center gap-1.5 text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded border border-orange-100" title="Requires Human Approval">
                            <UserCheck size={12} />
                            <span className="font-bold text-[10px]">HITL</span>
                        </div>
                    )}
                </div>

                {/* Handles with Labels */}
                <div className="absolute -left-3 top-1/2 -translate-y-12 flex items-center">
                    <Handle
                        type="target"
                        position={Position.Left}
                        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white transition-transform hover:scale-125"
                    />
                    <span className="text-[10px] ml-2 text-slate-400 bg-white px-1 opacity-0 group-hover:opacity-100 transition-opacity">Input</span>
                </div>

                <div className="absolute -right-3 top-1/2 -translate-y-12 flex items-center">
                    <span className="text-[10px] mr-2 text-slate-400 bg-white px-1 opacity-0 group-hover:opacity-100 transition-opacity">Response</span>
                    <Handle
                        type="source"
                        position={Position.Right}
                        id="output"
                        className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white transition-transform hover:scale-125"
                    />
                </div>
                <Handle
                    type="source"
                    position={Position.Bottom}
                    id="tool-call"
                    className="!w-3 !h-3 !bg-orange-500 !border-2 !border-white transition-transform hover:scale-125"
                    style={{ left: '50%' }}
                />

                {/* Tool Call Indicator */}
                <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] font-medium text-orange-600 opacity-0 group-hover:opacity-100 transition-opacity bg-orange-50 px-2 py-0.5 rounded-full border border-orange-100 whitespace-nowrap">
                    Tool Call
                </div>
            </div>

            <AgentConfigDialog
                open={configOpen}
                onOpenChange={setConfigOpen}
                data={data}
                onUpdate={(updates) => updateNodeData(id, updates)}
            />

            <TechnicalInfoDialog
                open={infoOpen}
                onOpenChange={setInfoOpen}
                data={{ ...data, id }}
            />
        </>
    );
}
