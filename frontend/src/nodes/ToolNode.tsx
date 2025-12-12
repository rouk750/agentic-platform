import { Handle, Position, useReactFlow, type NodeProps } from '@xyflow/react';
import { Wrench, Info, Loader2 } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useRunStore } from '../store/runStore';
import { useState } from 'react';
import { TechnicalInfoDialog } from './TechnicalInfoDialog';

export function ToolNode({ id, data, selected }: NodeProps) {
    const { updateNodeData } = useReactFlow();
    const activeNodeId = useRunStore((state) => state.activeNodeId);
    const currentToolName = useRunStore((state) => state.currentToolName);
    const isActive = id === activeNodeId;
    const isExecuting = !!currentToolName;
    const isEffectiveActive = isActive || isExecuting;
    const [infoOpen, setInfoOpen] = useState(false);

    return (
        <div
            className={twMerge(
                'bg-white border-2 rounded-xl w-64 shadow-sm transition-all duration-300 group',
                selected ? 'border-purple-500 ring-2 ring-purple-500/20 shadow-md' : 'border-slate-200 hover:border-slate-300',
                isEffectiveActive && 'border-purple-500 ring-4 ring-purple-500/20 shadow-xl scale-105'
            )}
        >
            {/* Header */}
            <div className="flex items-center gap-3 p-3 border-b border-slate-100 bg-gradient-to-b from-white to-slate-50/50 rounded-t-xl">
                <div className={twMerge(
                    "p-2 rounded-lg transition-colors",
                    isEffectiveActive ? "bg-purple-100 text-purple-600" : "bg-purple-50 text-purple-500"
                )}>
                    <Wrench size={18} />
                </div>

                <div className="flex-1 min-w-0">
                    <input
                        className="font-bold text-slate-800 bg-transparent border-none p-0 focus:ring-0 w-full text-sm truncate placeholder:text-slate-400"
                        value={String(data.label || "Tool Executor")}
                        onChange={(e) => updateNodeData(id, { label: e.target.value })}
                        placeholder="Tool Name"
                    />
                    <div className="text-[10px] text-slate-400 font-medium">
                        Executes active tools
                    </div>
                </div>

                <button
                    onClick={() => setInfoOpen(true)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                >
                    <Info size={16} />
                </button>
            </div>

            <TechnicalInfoDialog
                open={infoOpen}
                onOpenChange={setInfoOpen}
                data={{ ...data, id }}
            />

            {/* Content Area */}
            <div className="p-3 bg-slate-50/30 rounded-b-xl">
                {isEffectiveActive && currentToolName ? (
                    <div className="flex items-center gap-2 text-xs font-medium text-purple-600 animate-pulse">
                        <Loader2 size={12} className="animate-spin" />
                        <span>Executing {currentToolName}...</span>
                    </div>
                ) : (
                    <div className="text-xs text-slate-500 leading-relaxed">
                        Dynamically executes tools requested by the Agent and returns results.
                    </div>
                )}
            </div>

            {/* Handles */}
            <div className="absolute -left-3 top-1/2 -translate-y-5 flex items-center">
                <Handle
                    type="target"
                    position={Position.Left}
                    className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white transition-transform hover:scale-125"
                />
            </div>

            <div className="absolute -right-3 top-1/2 -translate-y-5 flex items-center">
                <Handle
                    type="source"
                    position={Position.Right}
                    className="!w-3 !h-3 !bg-purple-500 !border-2 !border-white transition-transform hover:scale-125"
                />
            </div>
        </div>
    );
}
