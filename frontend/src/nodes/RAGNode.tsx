import { Handle, Position, useReactFlow, type NodeProps } from '@xyflow/react';
import { Database, Info } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useState } from 'react';
import { TechnicalInfoDialog } from './TechnicalInfoDialog';

export function RAGNode({ id, selected, data }: NodeProps) {
    const { updateNodeData } = useReactFlow();
    const [infoOpen, setInfoOpen] = useState(false);

    return (
        <div
            className={twMerge(
                'bg-white border-2 rounded-lg w-48 shadow-md p-3',
                selected ? 'border-purple-500 ring-2 ring-purple-100' : 'border-slate-200'
            )}
        >
            <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 bg-purple-100 text-purple-600 rounded">
                    <Database size={16} />
                </div>
                <input
                    className="font-bold text-slate-700 bg-transparent border-none p-0 focus:ring-0 w-full text-sm truncate placeholder:text-slate-400"
                    value={String(data.label || "RAG Retriever")}
                    onChange={(e) => updateNodeData(id, { label: e.target.value })}
                    placeholder="RAG Name"
                />

                <button
                    onClick={() => setInfoOpen(true)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                >
                    <Info size={16} />
                </button>
            </div>

            <div className="text-xs text-slate-500">
                Retrieves documents from vector store and adds to context.
            </div>

            {/* Configuration Mock */}
            <div className="mt-2 text-[10px] bg-slate-50 p-1 rounded border border-slate-100 text-slate-400">
                Collection: {String(data.collection || "default")}
            </div>

            <div className="absolute -left-3 top-1/2 -translate-y-6 flex items-center">
                <Handle
                    type="target"
                    position={Position.Left}
                    className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white"
                />
                <span className="text-[10px] ml-2 text-slate-400 bg-white px-1">Query</span>
            </div>

            <div className="absolute -right-3 top-1/2 -translate-y-6 flex items-center">
                <span className="text-[10px] mr-2 text-slate-400 bg-white px-1">Context</span>
                <Handle
                    type="source"
                    position={Position.Right}
                    className="!w-3 !h-3 !bg-purple-500 !border-2 !border-white"
                />
            </div>

            <TechnicalInfoDialog
                open={infoOpen}
                onOpenChange={setInfoOpen}
                data={{ ...data, id }}
            />
        </div>
    );
}
