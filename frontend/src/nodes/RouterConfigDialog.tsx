import * as Dialog from '@radix-ui/react-dialog';
import { X, Plus, Trash2, GitFork } from 'lucide-react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useEffect } from 'react';
import { RouterNodeData, RouteCondition } from '../types/router';

interface RouterConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    data: RouterNodeData;
    onUpdate: (data: Partial<RouterNodeData>) => void;
}

type FormData = {
    routes: RouteCondition[];
};

export function RouterConfigDialog({ open, onOpenChange, data, onUpdate }: RouterConfigDialogProps) {
    const { control, register, handleSubmit, reset, watch } = useForm<FormData>({
        defaultValues: {
            routes: data.routes || []
        }
    });

    const { fields, append, remove } = useFieldArray<FormData>({
        control,
        name: "routes"
    });

    const watchedRoutes = watch("routes");

    useEffect(() => {
        if (open) {
            reset({
                routes: (data.routes || []).map((r: any) => ({
                    ...r,
                    source: r.source || 'message' // default to message for backward compat
                }))
            });
        }
    }, [open, data, reset]);

    const onSubmit = (formData: FormData) => {
        // Ensure every route has a target_handle and id if missing
        const processedRoutes = formData.routes.map((route, index) => {
            const handleId = route.target_handle || `route - ${Date.now()} -${index} `;
            return {
                ...route,
                id: handleId, // simplified: use handle as id for this context
                target_handle: handleId
            };
        });

        const updates: Partial<RouterNodeData> = {
            routes: processedRoutes
        };

        onUpdate(updates);
        onOpenChange(false);
    };

    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm" />
                <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-3xl bg-white rounded-xl shadow-2xl z-50 p-6 border border-slate-200">
                    <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-2">
                            <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                                <GitFork size={20} />
                            </div>
                            <Dialog.Title className="text-xl font-bold text-slate-800">Router Configuration</Dialog.Title>
                        </div>
                        <Dialog.Close className="text-slate-400 hover:text-slate-600">
                            <X size={20} />
                        </Dialog.Close>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">

                        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                            <div className="flex justify-between items-center">
                                <label className="text-sm font-semibold text-slate-700">Routes</label>
                                <button
                                    type="button"
                                    onClick={() => append({ id: '', source: 'message', condition: 'contains', value: '', target_handle: '' })}
                                    className="text-xs flex items-center gap-1 text-purple-600 hover:text-purple-700 font-medium px-2 py-1 bg-purple-50 hover:bg-purple-100 rounded transition-colors"
                                >
                                    <Plus size={14} /> Add Route
                                </button>
                            </div>

                            {fields.length === 0 && (
                                <div className="text-center py-8 border-2 border-dashed border-slate-200 rounded-lg text-slate-400 text-sm">
                                    No routes defined. Messages will go to Default.
                                </div>
                            )}

                            <div className="space-y-3">
                                {fields.map((field, index) => {
                                    const currentSource = watchedRoutes?.[index]?.source || 'message';

                                    return (
                                        <div key={field.id} className="flex items-start gap-2 p-3 bg-slate-50 border border-slate-200 rounded-lg group">
                                            <div className="flex-1 space-y-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-bold text-slate-400 w-6">#{index + 1}</span>

                                                    {/* Source Selector */}
                                                    <div className="flex flex-col">
                                                        <label className="text-[10px] text-slate-400 font-semibold mb-0.5">Source</label>
                                                        <select
                                                            {...register(`routes.${index}.source`)}
                                                            className="text-xs p-1.5 rounded border border-slate-300 bg-white focus:border-purple-500 outline-none w-24"
                                                        >
                                                            <option value="message">Message</option>
                                                            <option value="context">Context</option>
                                                        </select>
                                                    </div>

                                                    {/* Context Key Input */}
                                                    {currentSource === 'context' && (
                                                        <div className="flex flex-col">
                                                            <label className="text-[10px] text-slate-400 font-semibold mb-0.5">Variable Name</label>
                                                            <input
                                                                {...register(`routes.${index}.context_key`)}
                                                                placeholder="e.g. score"
                                                                className="text-xs p-1.5 rounded border border-slate-300 focus:border-purple-500 outline-none w-28"
                                                            />
                                                        </div>
                                                    )}

                                                    {/* Condition */}
                                                    <div className="flex flex-col">
                                                        <label className="text-[10px] text-slate-400 font-semibold mb-0.5">Condition</label>
                                                        <select
                                                            {...register(`routes.${index}.condition` as const)}
                                                            className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white focus:border-purple-500 outline-none"
                                                        >
                                                            <option value="equals">Equals</option>
                                                            <option value="contains">Contains</option>
                                                            <option value="regex">Regex</option>
                                                        </select>
                                                    </div>

                                                    {/* Value */}
                                                    <div className="flex flex-col flex-1">
                                                        <label className="text-[10px] text-slate-400 font-semibold mb-0.5">Value</label>
                                                        <input
                                                            {...register(`routes.${index}.value`)}
                                                            placeholder="Value to match..."
                                                            className="flex-1 text-xs p-1.5 rounded border border-slate-300 focus:border-purple-500 outline-none"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => remove(index)}
                                                className="mt-5 p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="flex justify-end gap-3 mt-2 pt-4 border-t border-slate-100">
                            <button
                                type="button"
                                onClick={() => onOpenChange(false)}
                                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg shadow-sm transition-colors"
                            >
                                Save Routes
                            </button>
                        </div>
                    </form>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}
