import { Handle, Position, useReactFlow, type NodeProps, type Node } from '@xyflow/react';
import { SmartNodeConfigDialog } from './SmartNodeConfigDialog';
import { TechnicalInfoDialog } from './TechnicalInfoDialog';
import { Sparkles, Settings2, Brain, Zap, Info } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useState } from 'react';
import { useRunStore } from '../store/runStore';
import type { SmartNodeData, SmartNodeMode } from '../types/smartNode';

type SmartNodeType = Node<SmartNodeData>;

export function SmartNode({ id, data, selected }: NodeProps<SmartNodeType>) {
    const { updateNodeData } = useReactFlow();
    const activeNodeId = useRunStore((state) => state.activeNodeId);
    const isActive = id === activeNodeId;
    const [configOpen, setConfigOpen] = useState(false);
    const [infoOpen, setInfoOpen] = useState(false);

    const mode = (data.mode as SmartNodeMode) || "ChainOfThought"; // Default
    const inputs = data.inputs || [];
    const outputs = data.outputs || [];

    return (
        <>
            <div
                className={twMerge(
                    'bg-white border-2 rounded-xl w-72 shadow-sm transition-all duration-300 group',
                    selected ? 'border-amber-500 ring-2 ring-amber-500/20 shadow-md' : 'border-slate-200 hover:border-slate-300',
                    isActive && 'border-green-500 ring-4 ring-green-500/20 shadow-xl scale-105'
                )}
            >
                {/* Header */}
                <div className="flex items-center gap-3 p-3 border-b border-amber-100 bg-gradient-to-b from-amber-50/50 to-amber-100/30 rounded-t-xl">
                    <div className={twMerge(
                        "p-2 rounded-lg transition-colors bg-amber-100 text-amber-600"
                    )}>
                        <Sparkles size={18} />
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                            <input
                                className="font-bold text-slate-800 bg-transparent border-none p-0 focus:ring-0 w-full text-sm truncate placeholder:text-slate-400"
                                value={String(data.label || "Smart Node")}
                                onChange={(e) => updateNodeData(id, { label: e.target.value })}
                                placeholder="Smart Node"
                            />
                            <span className="text-[9px] font-bold bg-amber-200 text-amber-700 px-1 py-0.5 rounded uppercase tracking-wide">Beta</span>
                        </div>

                        <div className="text-[10px] text-slate-500 font-medium flex items-center gap-1 mt-0.5">
                            {mode === 'ChainOfThought' ? <Brain size={10} /> : <Zap size={10} />}
                            <span className="truncate">{mode === 'ChainOfThought' ? "Reasoning Mode" : "Predict Mode"}</span>
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
                <div className="p-3">
                    {/* Goal/Instructions Snippet */}
                    <div
                        className="text-xs text-slate-600 italic border-l-2 border-amber-200 pl-2 py-1 mb-3 bg-slate-50/50 rounded-r line-clamp-3 overflow-hidden text-ellipsis"
                        title={String(data.goal || '')}
                    >
                        &quot;{String(data.goal || 'Define a goal...')}&quot;
                    </div>

                    {/* Signature Viz */}
                    <div className="flex gap-2 text-[10px] font-mono">
                        <div className="flex-1 bg-blue-50 border border-blue-100 rounded px-2 py-1">
                            <div className="uppercase text-blue-400 font-bold mb-1 flex items-center gap-1">
                                Inputs
                            </div>
                            <div className="flex flex-col gap-0.5 text-slate-700">
                                {inputs.length > 0 ? inputs.map((i, idx) => (
                                    <span key={idx} className="truncate">• {i.name}</span>
                                )) : <span className="text-slate-400 opacity-50">None</span>}
                            </div>
                        </div>

                        <div className="flex items-center text-slate-300">→</div>

                        <div className="flex-1 bg-green-50 border border-green-100 rounded px-2 py-1">
                            <div className="uppercase text-green-500 font-bold mb-1 flex items-center gap-1">
                                Outputs
                            </div>
                            <div className="flex flex-col gap-0.5 text-slate-700">
                                {outputs.length > 0 ? outputs.map((o, idx) => (
                                    <span key={idx} className="truncate">• {o.name}</span>
                                )) : <span className="text-slate-400 opacity-50">None</span>}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Handles */}
                <div className="absolute -left-3 top-1/2 -translate-y-4 flex items-center">
                    <Handle
                        type="target"
                        position={Position.Left}
                        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white transition-transform hover:scale-125"
                    />
                </div>
                <div className="absolute -right-3 top-1/2 -translate-y-4 flex items-center">
                    <Handle
                        type="source"
                        position={Position.Right}
                        className="!w-3 !h-3 !bg-green-500 !border-2 !border-white transition-transform hover:scale-125"
                    />
                </div>
            </div>

            <SmartNodeConfigDialog
                open={configOpen}
                onOpenChange={setConfigOpen}
                data={{ ...data, id }}
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
