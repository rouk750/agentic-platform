import { useState, useEffect } from 'react';
import { X, Bot, Sparkles, Loader2, Save, Plus, Trash2, Box, Brain, Zap } from 'lucide-react';
import { useForm, useFieldArray } from 'react-hook-form';
import { AgentTemplate } from '../api/templates';
import { toast } from 'sonner';
import { getModels } from '../api/settings';
import type { LLMProfile } from '../types/settings';
import { ToolSelector } from '../nodes/ToolSelector';
import type { SchemaField } from '../types/common';
import { getAvailableGuardrails, type GuardrailDefinition } from '../api/smartNode';

interface AgentTemplateDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (template: Partial<AgentTemplate>) => Promise<void>;
    initialData?: AgentTemplate | null;
}

type AgentFormData = {
    modelId: string;
    system_prompt: string;
    max_iterations: number;
    output_schema: SchemaField[];
    flexible_mode: boolean;
};

type SmartNodeFormData = {
    goal: string;
    mode: string;
    inputs: { name: string; desc: string }[];
    outputs: { name: string; desc: string; guardrails?: any[] }[];
    llm_profile: string;
};

export default function AgentTemplateDialog({ isOpen, onClose, onSave, initialData }: AgentTemplateDialogProps) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [type, setType] = useState<'agent' | 'smart_node'>('agent');
    const [loading, setLoading] = useState(false);
    const [modelsLoading, setModelsLoading] = useState(false);
    const [models, setModels] = useState<LLMProfile[]>([]);
    const [selectedTools, setSelectedTools] = useState<string[]>([]);
    const [availableGuardrails, setAvailableGuardrails] = useState<GuardrailDefinition[]>([]);

    // Agent Form
    const agentForm = useForm<AgentFormData>({
        defaultValues: {
            modelId: '',
            system_prompt: '',
            max_iterations: 0,
            output_schema: [],
            flexible_mode: false
        }
    });

    const { fields: schemaFields, append: appendSchema, remove: removeSchema } = useFieldArray({
        control: agentForm.control,
        name: "output_schema"
    });

    // Smart Node Form
    const smartNodeForm = useForm<SmartNodeFormData>({
        defaultValues: {
            goal: '',
            mode: 'ChainOfThought',
            inputs: [{ name: 'input', desc: 'Main input' }],
            outputs: [{ name: 'output', desc: 'Main output' }],
            llm_profile: ''
        }
    });

    const { fields: inputFields, append: appendInput, remove: removeInput } = useFieldArray({
        control: smartNodeForm.control,
        name: "inputs"
    });

    const { fields: outputFields, append: appendOutput, remove: removeOutput } = useFieldArray({
        control: smartNodeForm.control,
        name: "outputs"
    });

    useEffect(() => {
        if (isOpen) {
            setModelsLoading(true);
            Promise.all([
                getModels().then(setModels),
                getAvailableGuardrails().then(setAvailableGuardrails)
            ]).finally(() => setModelsLoading(false));

            if (initialData) {
                setName(initialData.name);
                setDescription(initialData.description || '');
                setType(initialData.type as 'agent' | 'smart_node');

                try {
                    const config = JSON.parse(initialData.config);

                    if (initialData.type === 'agent') {
                        agentForm.reset({
                            modelId: config.modelId || config.profile_id?.toString() || '',
                            system_prompt: config.system_prompt || '',
                            max_iterations: config.max_iterations || 0,
                            output_schema: config.output_schema || [],
                            flexible_mode: config.flexible_mode || false
                        });
                        setSelectedTools(config.tools || []);
                    } else {
                        smartNodeForm.reset({
                            goal: config.goal || '',
                            mode: config.mode || 'ChainOfThought',
                            inputs: config.inputs || [{ name: 'input', desc: 'Main input' }],
                            outputs: config.outputs || [{ name: 'output', desc: 'Main output' }],
                            llm_profile: config.llm_profile?.id?.toString() || config.llm_profile || ''
                        });
                    }
                } catch (e) {
                    console.error('Failed to parse template config', e);
                }
            } else {
                setName('');
                setDescription('');
                setType('agent');
                agentForm.reset({
                    modelId: '',
                    system_prompt: '',
                    max_iterations: 0,
                    output_schema: [],
                    flexible_mode: false
                });
                smartNodeForm.reset({
                    goal: '',
                    mode: 'ChainOfThought',
                    inputs: [{ name: 'input', desc: 'Main input' }],
                    outputs: [{ name: 'output', desc: 'Main output' }],
                    llm_profile: ''
                });
                setSelectedTools([]);
            }
        }
    }, [isOpen, initialData, agentForm, smartNodeForm]);

    const handleSave = async () => {
        if (!name.trim()) {
            toast.error("Name is required");
            return;
        }

        try {
            setLoading(true);
            let configData: any = {};

            if (type === 'agent') {
                const formData = agentForm.getValues();
                const selectedModel = models.find(m => String(m.id) === formData.modelId);

                configData = {
                    system_prompt: formData.system_prompt,
                    max_iterations: Number(formData.max_iterations),
                    tools: selectedTools,
                    output_schema: formData.output_schema,
                    flexible_mode: formData.flexible_mode
                };

                if (selectedModel) {
                    configData.profile_id = selectedModel.id;
                    configData.modelId = String(selectedModel.id);
                    configData.modelName = selectedModel.name;
                    configData.provider = selectedModel.provider;
                    configData.model_id = selectedModel.model_id;
                }
            } else {
                const formData = smartNodeForm.getValues();
                const selectedModel = models.find(m => String(m.id) === formData.llm_profile);

                configData = {
                    goal: formData.goal,
                    mode: formData.mode,
                    inputs: formData.inputs,
                    outputs: formData.outputs,
                    llm_profile: selectedModel || null
                };
            }

            await onSave({
                name,
                description,
                type,
                config: JSON.stringify(configData)
            });
            onClose();
        } catch (error) {
            console.error("Failed to save template", error);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    const isFlexible = agentForm.watch('flexible_mode');
    const selectedMode = smartNodeForm.watch('mode');

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[90vh]">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                    <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                        {initialData ? 'Edit Template' : 'New Template'}
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 text-slate-500 rounded-full transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-5 overflow-y-auto">
                    {/* Type Selection */}
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={() => !initialData && setType('agent')}
                            disabled={!!initialData}
                            className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${type === 'agent' ? 'border-blue-500 bg-blue-50/50 text-blue-700' : 'border-slate-100 bg-white text-slate-500 hover:border-slate-200'} ${initialData ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            <Bot size={24} />
                            <span className="font-semibold text-sm">AI Agent</span>
                        </button>
                        <button
                            onClick={() => !initialData && setType('smart_node')}
                            disabled={!!initialData}
                            className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${type === 'smart_node' ? 'border-amber-500 bg-amber-50/50 text-amber-700' : 'border-slate-100 bg-white text-slate-500 hover:border-slate-200'} ${initialData ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            <Sparkles size={24} />
                            <span className="font-semibold text-sm">Smart Node</span>
                        </button>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Name</label>
                        <input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder={type === 'agent' ? "e.g., Support Agent" : "e.g., Summarizer Node"}
                            className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-slate-700 text-sm font-medium transition-all"
                        />
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Description</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="What does this template do?"
                            rows={2}
                            className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-slate-700 text-sm transition-all resize-none"
                        />
                    </div>

                    <div className="h-px bg-slate-200 my-4"></div>

                    {/* Configuration Forms */}
                    {type === 'agent' ? (
                        <div className="space-y-4">
                            <h3 className="text-sm font-bold text-slate-700">Agent Configuration</h3>

                            {/* Model Selection */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">Model</label>
                                {modelsLoading ? (
                                    <div className="flex items-center gap-2 text-sm text-slate-500">
                                        <Loader2 className="animate-spin" size={16} /> Loading models...
                                    </div>
                                ) : (
                                    <select
                                        {...agentForm.register('modelId')}
                                        className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                    >
                                        <option value="">Select a model...</option>
                                        {models.map(m => (
                                            <option key={m.id} value={m.id}>
                                                {m.name} ({m.provider})
                                            </option>
                                        ))}
                                    </select>
                                )}
                            </div>

                            {/* System Prompt */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">System Prompt (Persona)</label>
                                <textarea
                                    {...agentForm.register('system_prompt')}
                                    className="w-full p-3 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all min-h-[100px] resize-y"
                                    placeholder="You are an expert coding assistant..."
                                />
                            </div>

                            {/* Max Iterations */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">Max Iterations (Loop Protection)</label>
                                <input
                                    type="number"
                                    {...agentForm.register('max_iterations')}
                                    className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                    placeholder="0 for infinite"
                                    min={0}
                                />
                                <p className="text-xs text-slate-500">Maximum number of messages this agent can send in a single run. Set to 0 for no limit.</p>
                            </div>

                            {/* Tools */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">Tools</label>
                                <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                                    <ToolSelector
                                        selectedTools={selectedTools}
                                        onChange={setSelectedTools}
                                    />
                                </div>
                            </div>

                            {/* Structured Output Schema */}
                            <div className="space-y-3 pt-4 border-t border-slate-100">
                                <div className="flex justify-between items-center">
                                    <div>
                                        <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                                            <Box size={16} className="text-purple-600" />
                                            Structured Output (JSON)
                                        </label>
                                        <p className="text-xs text-slate-500 mt-1">
                                            Define keys to force the agent to output structured data.
                                        </p>
                                    </div>
                                    {!isFlexible && (
                                        <button
                                            type="button"
                                            onClick={() => appendSchema({ name: '', description: '', type: 'string' })}
                                            className="text-xs flex items-center gap-1 text-purple-600 hover:text-purple-700 font-medium px-2 py-1 bg-purple-50 hover:bg-purple-100 rounded transition-colors"
                                        >
                                            <Plus size={14} /> Add Field
                                        </button>
                                    )}
                                </div>

                                {/* Flexible Mode Toggle */}
                                <div className="flex items-center gap-2 mb-2 px-1">
                                    <input
                                        type="checkbox"
                                        id="flexible_mode"
                                        {...agentForm.register('flexible_mode')}
                                        className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                                    />
                                    <label htmlFor="flexible_mode" className="text-sm text-slate-700 font-medium cursor-pointer">
                                        Flexible JSON (Orchestrator Mode)
                                    </label>
                                </div>

                                {isFlexible ? (
                                    <div className="p-3 bg-purple-50 border border-purple-100 rounded-lg text-xs text-purple-700">
                                        <strong>Orchestrator Mode Active:</strong> Use your System Prompt to define the different JSON structures the agent can return.
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        {schemaFields.length === 0 && (
                                            <div className="text-center py-4 border-2 border-dashed border-slate-200 rounded-lg text-slate-400 text-xs">
                                                No schema defined. Agent returns plain text.
                                            </div>
                                        )}
                                        {schemaFields.map((field, index) => (
                                            <div key={field.id} className="flex items-start gap-2 p-2 bg-slate-50 border border-slate-200 rounded-lg">
                                                <div className="flex-1 grid grid-cols-12 gap-2">
                                                    <div className="col-span-4">
                                                        <input
                                                            {...agentForm.register(`output_schema.${index}.name` as const)}
                                                            placeholder="Key Name (e.g. sentiment)"
                                                            className="w-full text-xs p-1.5 rounded border border-slate-300 focus:border-purple-500 outline-none"
                                                        />
                                                    </div>
                                                    <div className="col-span-3">
                                                        <select
                                                            {...agentForm.register(`output_schema.${index}.type` as const)}
                                                            className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white focus:border-purple-500 outline-none"
                                                        >
                                                            <option value="string">String</option>
                                                            <option value="number">Number</option>
                                                            <option value="boolean">Boolean</option>
                                                            <option value="array">Array</option>
                                                        </select>
                                                    </div>
                                                    <div className="col-span-5">
                                                        <input
                                                            {...agentForm.register(`output_schema.${index}.description` as const)}
                                                            placeholder="Description..."
                                                            className="w-full text-xs p-1.5 rounded border border-slate-300 focus:border-purple-500 outline-none"
                                                        />
                                                    </div>
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => removeSchema(index)}
                                                    className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2">
                                <span className="text-amber-600 bg-amber-50 px-2 py-1 rounded text-[10px] uppercase tracking-wide flex items-center gap-1">
                                    <Sparkles size={10} /> Beta
                                </span>
                                Smart Node Configuration
                            </h3>

                            {/* Model Selection */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">LLM Profile</label>
                                {modelsLoading ? (
                                    <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 size={16} className="animate-spin" /> Loading...</div>
                                ) : (
                                    <select
                                        {...smartNodeForm.register('llm_profile')}
                                        className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
                                    >
                                        <option value="">Select a model...</option>
                                        {models.map(m => (
                                            <option key={m.id} value={m.id?.toString()}>
                                                {m.name} ({m.provider})
                                            </option>
                                        ))}
                                    </select>
                                )}
                            </div>

                            {/* Mode Selection */}
                            <div className="space-y-3">
                                <label className="text-sm font-semibold text-slate-700">Reasoning Mode (DSPy Module)</label>
                                <div className="grid grid-cols-2 gap-4">
                                    <div
                                        className={`cursor-pointer border-2 rounded-xl p-4 flex flex-col gap-2 transition-all ${selectedMode === 'ChainOfThought' ? 'border-amber-500 bg-amber-50/50 ring-1 ring-amber-500/20' : 'border-slate-200 hover:border-slate-300'}`}
                                        onClick={() => smartNodeForm.setValue('mode', 'ChainOfThought')}
                                    >
                                        <div className="flex items-center gap-2 font-semibold text-amber-700">
                                            <Brain size={18} />
                                            ChainOfThought
                                        </div>
                                        <p className="text-xs text-slate-500">Best for reasoning, explanation, and complex tasks.</p>
                                    </div>

                                    <div
                                        className={`cursor-pointer border-2 rounded-xl p-4 flex flex-col gap-2 transition-all ${selectedMode === 'Predict' ? 'border-blue-500 bg-blue-50/50 ring-1 ring-blue-500/20' : 'border-slate-200 hover:border-slate-300'}`}
                                        onClick={() => smartNodeForm.setValue('mode', 'Predict')}
                                    >
                                        <div className="flex items-center gap-2 font-semibold text-blue-700">
                                            <Zap size={18} />
                                            Predict
                                        </div>
                                        <p className="text-xs text-slate-500">Best for simple extraction, classification. Faster.</p>
                                    </div>
                                </div>
                            </div>

                            {/* Goal */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">Goal / Instructions</label>
                                <textarea
                                    {...smartNodeForm.register('goal')}
                                    placeholder="Describe what this node should do. Be specific."
                                    className="w-full p-3 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all h-24 resize-none font-mono"
                                />
                                <p className="text-[10px] text-slate-400">This will be compiled into the DSPy signature instructions.</p>
                            </div>

                            {/* Inputs & Outputs */}
                            <div className="grid grid-cols-2 gap-8 border-t border-slate-100 pt-6">
                                {/* Inputs */}
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-semibold text-blue-600">Inputs</label>
                                        <button type="button" className="text-xs flex items-center gap-1 text-slate-600 hover:text-blue-600 border border-slate-200 hover:border-blue-200 px-2 py-1 rounded transition-colors" onClick={() => appendInput({ name: '', desc: '' })}>
                                            <Plus size={14} /> Add
                                        </button>
                                    </div>
                                    <div className="space-y-2">
                                        {inputFields.map((field, index) => (
                                            <div key={field.id} className="flex gap-2 items-start">
                                                <div className="grid gap-1 flex-1">
                                                    <input {...smartNodeForm.register(`inputs.${index}.name`)} placeholder="Field name" className="w-full text-xs p-1.5 rounded border border-slate-300 font-mono focus:border-blue-500 outline-none" />
                                                    <input {...smartNodeForm.register(`inputs.${index}.desc`)} placeholder="Description" className="w-full text-xs p-1.5 rounded border border-slate-300 focus:border-blue-500 outline-none" />
                                                </div>
                                                <button type="button" className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors" onClick={() => removeInput(index)}>
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Outputs */}
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-semibold text-green-600">Outputs</label>
                                        <button type="button" className="text-xs flex items-center gap-1 text-slate-600 hover:text-green-600 border border-slate-200 hover:border-green-200 px-2 py-1 rounded transition-colors" onClick={() => appendOutput({ name: '', desc: '' })}>
                                            <Plus size={14} /> Add
                                        </button>
                                    </div>
                                    <div className="space-y-2">
                                        {outputFields.map((field, index) => (
                                            <div key={field.id} className="flex gap-2 items-start">
                                                <div className="grid gap-1 flex-1">
                                                    <input {...smartNodeForm.register(`outputs.${index}.name`)} placeholder="Field name" className="w-full text-xs p-1.5 rounded border border-slate-300 font-mono focus:border-green-500 outline-none" />
                                                    <input {...smartNodeForm.register(`outputs.${index}.desc`)} placeholder="Description" className="w-full text-xs p-1.5 rounded border border-slate-300 focus:border-green-500 outline-none" />
                                                </div>
                                                <button type="button" className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors" onClick={() => removeOutput(index)}>
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-slate-600 font-medium text-sm hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={loading || !name.trim()}
                        className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white font-medium text-sm rounded-lg hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                        {initialData ? 'Update Template' : 'Create Template'}
                    </button>
                </div>
            </div>
        </div>
    );
}
