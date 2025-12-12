import * as Dialog from '@radix-ui/react-dialog';
import { X, Loader2, Plus, Trash2, Box } from 'lucide-react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { getModels, LLMProfile } from '../api/settings';
import { ToolSelector } from './ToolSelector';

interface AgentConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    data: any;
    onUpdate: (data: any) => void;
}

type SchemaField = {
    name: string;
    description: string;
    type: string;
};

type FormData = {
    modelId: string;
    system_prompt: string;
    max_iterations: number;
    output_schema: SchemaField[];
    flexible_mode: boolean;
};

export function AgentConfigDialog({ open, onOpenChange, data, onUpdate }: AgentConfigDialogProps) {
    const { register, control, handleSubmit, setValue, watch, reset } = useForm<FormData>({
        defaultValues: {
            modelId: data.modelId ? String(data.modelId) : "",
            system_prompt: data.system_prompt || "",
            max_iterations: data.max_iterations || 0,
            output_schema: data.output_schema || [],
            flexible_mode: data.flexible_mode || false
        }
    });

    const { fields, append, remove } = useFieldArray({
        control,
        name: "output_schema"
    });

    const [models, setModels] = useState<LLMProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTools, setSelectedTools] = useState<string[]>(data.tools || []);

    useEffect(() => {
        if (open) {
            setLoading(true);
            getModels()
                .then(setModels)
                .finally(() => setLoading(false));

            // Sync form with data when opened
            setValue('modelId', data.modelId ? String(data.modelId) : "");
            setValue('system_prompt', data.system_prompt || "");
            setValue('max_iterations', data.max_iterations || 0);
            setValue('output_schema', data.output_schema || []);
            setValue('flexible_mode', data.flexible_mode || false);
            setSelectedTools(data.tools || []);
        }
    }, [open, data, setValue]);

    const onSubmit = (formData: FormData, shouldClose: boolean = true) => {
        const selectedModel = models.find(m => String(m.id) === formData.modelId);

        const updates: any = {
            system_prompt: formData.system_prompt,
            max_iterations: Number(formData.max_iterations),
            tools: selectedTools,
            output_schema: formData.output_schema,
            flexible_mode: formData.flexible_mode
        };

        if (selectedModel) {
            updates.profile_id = selectedModel.id; // Critical: Backend expects profile_id
            updates.modelId = selectedModel.id;
            updates.modelName = selectedModel.name;
            updates.provider = selectedModel.provider;
            updates.model_id = selectedModel.model_id;
        }

        onUpdate(updates);

        if (shouldClose) {
            onOpenChange(false);
        } else {
            toast.success("Agent configuration saved");
        }
    };

    const isFlexible = watch('flexible_mode');

    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm" />
                <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-white rounded-xl shadow-2xl z-50 p-6 border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
                    <div className="flex justify-between items-center mb-6 shrink-0">
                        <Dialog.Title className="text-xl font-bold text-slate-800">Agent Configuration</Dialog.Title>
                        <Dialog.Close className="text-slate-400 hover:text-slate-600">
                            <X size={20} />
                        </Dialog.Close>
                    </div>

                    <form onSubmit={handleSubmit((data) => onSubmit(data, true))} className="flex flex-col gap-6 overflow-y-auto pr-2">
                        {/* Model Selection */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Model</label>
                            {loading ? (
                                <div className="flex items-center gap-2 text-sm text-slate-500">
                                    <Loader2 className="animate-spin" size={16} /> Loading models...
                                </div>
                            ) : (
                                <select
                                    {...register('modelId')}
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
                                {...register('system_prompt')}
                                className="w-full p-3 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all min-h-[100px] resize-y"
                                placeholder="You are an expert coding assistant..."
                            />
                        </div>

                        {/* Max Iterations */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Max Iterations (Loop Protection)</label>
                            <input
                                type="number"
                                {...register('max_iterations')}
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
                                        Define keys to force the agent to output structured data into the Context.
                                    </p>
                                </div>
                                {!isFlexible && (
                                    <button
                                        type="button"
                                        onClick={() => append({ name: '', description: '', type: 'string' })}
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
                                    {...register('flexible_mode')}
                                    className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                                />
                                <label htmlFor="flexible_mode" className="text-sm text-slate-700 font-medium cursor-pointer">
                                    Flexible JSON (Orchestrator Mode)
                                </label>
                            </div>

                            {isFlexible ? (
                                <div className="p-3 bg-purple-50 border border-purple-100 rounded-lg text-xs text-purple-700">
                                    <strong>Orchestrator Mode Active:</strong> Use your System Prompt to define the different JSON structures the agent can return (e.g. <code>{"{"}type: "search", ...{"}"}</code> vs <code>{"{"}type: "answer", ...{"}"}</code>).
                                    <br />The agent will output raw JSON without a forced schema validation loop.
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {fields.length === 0 && (
                                        <div className="text-center py-4 border-2 border-dashed border-slate-200 rounded-lg text-slate-400 text-xs">
                                            No schema defined. Agent returns plain text.
                                        </div>
                                    )}
                                    {fields.map((field, index) => (
                                        <div key={field.id} className="flex items-start gap-2 p-2 bg-slate-50 border border-slate-200 rounded-lg">
                                            <div className="flex-1 grid grid-cols-12 gap-2">
                                                <div className="col-span-4">
                                                    <input
                                                        {...register(`output_schema.${index}.name` as const)}
                                                        placeholder="Key Name (e.g. sentiment)"
                                                        className="w-full text-xs p-1.5 rounded border border-slate-300 focus:border-purple-500 outline-none"
                                                    />
                                                </div>
                                                <div className="col-span-3">
                                                    <select
                                                        {...register(`output_schema.${index}.type` as const)}
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
                                                        {...register(`output_schema.${index}.description` as const)}
                                                        placeholder="Description..."
                                                        className="w-full text-xs p-1.5 rounded border border-slate-300 focus:border-purple-500 outline-none"
                                                    />
                                                </div>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => remove(index)}
                                                className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-100 shrink-0">
                            <button
                                type="button"
                                onClick={() => onOpenChange(false)}
                                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={handleSubmit((data) => onSubmit(data, false))}
                                className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                            >
                                Save
                            </button>
                            <button
                                type="button"
                                onClick={handleSubmit((data) => onSubmit(data, true))}
                                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
                            >
                                Save & Close
                            </button>
                        </div>
                    </form>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}
