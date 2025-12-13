import { Trash2, Bot, Server } from 'lucide-react';
import type { LLMProfile } from '../../types/settings';

interface ModelListProps {
    models: LLMProfile[];
    onDelete: (id: number) => void;
}

export function ModelList({ models, onDelete }: ModelListProps) {
    if (models.length === 0) {
        return (
            <div className="text-center py-10 text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg border border-dashed border-zinc-200 dark:border-zinc-700">
                <Server className="mx-auto mb-2 opacity-50" size={32} />
                <p>No models configured yet.</p>
            </div>
        );
    }

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {models.map((model) => (
                <div key={model.id} className="group relative bg-slate-100 border border-slate-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start">
                        <div className="flex items-start gap-3">
                            <div className="p-2 bg-white rounded-md border border-slate-200">
                                <Bot className="text-blue-600" size={24} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-800">{model.name}</h3>
                                <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mt-1">
                                    {model.provider}
                                </p>
                                <code className="text-xs bg-white border border-slate-200 px-1.5 py-0.5 rounded mt-2 inline-block text-slate-600">
                                    {model.model_id}
                                </code>
                            </div>
                        </div>
                        <button
                            onClick={() => onDelete(model.id)}
                            className="text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100 p-1"
                            aria-label="Delete model"
                        >
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}
