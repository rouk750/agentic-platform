import { Trash2, Bot, Server, Edit2, Loader2, Wifi } from 'lucide-react';
import type { LLMProfile } from '../../types/settings';
import { useState } from 'react';

interface ModelListProps {
  models: LLMProfile[];
  onDelete: (id: number) => void;
  onEdit: (model: LLMProfile) => void;
  onTest: (id: number) => Promise<boolean>;
}

export function ModelList({ models, onDelete, onEdit, onTest }: ModelListProps) {
  const [testingId, setTestingId] = useState<number | null>(null);

  const handleTest = async (id: number) => {
    setTestingId(id);
    await onTest(id);
    setTestingId(null);
  };

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
        <div
          key={model.id}
          className="group relative bg-slate-100 border border-slate-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow flex flex-col"
        >
          <div className="flex-1 flex items-start gap-3 mb-4">
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

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleTest(model.id)}
              disabled={testingId === model.id}
              className="bg-white border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-200 transition-colors p-1.5 rounded-md shadow-sm"
              title="Test Connectivity"
            >
              {testingId === model.id ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Wifi size={16} />
              )}
            </button>
            <button
              onClick={() => onEdit(model)}
              className="bg-white border border-slate-200 text-slate-500 hover:text-slate-800 hover:border-slate-300 transition-colors p-1.5 rounded-md shadow-sm"
              title="Edit Configuration"
            >
              <Edit2 size={16} />
            </button>
            <button
              onClick={() => onDelete(model.id)}
              className="bg-white border border-slate-200 text-slate-500 hover:text-red-500 hover:border-red-200 transition-colors p-1.5 rounded-md shadow-sm"
              title="Delete model"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
