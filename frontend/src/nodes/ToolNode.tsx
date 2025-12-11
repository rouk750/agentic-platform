import { Handle, Position, NodeProps } from '@xyflow/react';
import { Wrench } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useRunStore } from '../store/runStore';

export function ToolNode({ id, selected }: NodeProps) {
    const activeNodeId = useRunStore((state) => state.activeNodeId);
    const isActive = id === activeNodeId;

    return (
        <div
            className={twMerge(
                'bg-white border-2 rounded-xl w-64 shadow-sm transition-all duration-300 group',
                selected ? 'border-purple-500 ring-2 ring-purple-500/20 shadow-md' : 'border-slate-200 hover:border-slate-300',
                isActive && 'border-purple-500 ring-4 ring-purple-500/20 shadow-xl scale-105'
            )}
        >
            {/* Header */}
            <div className="flex items-center gap-3 p-3 border-b border-slate-100 bg-gradient-to-b from-white to-slate-50/50 rounded-t-xl">
                <div className={twMerge(
                    "p-2 rounded-lg transition-colors",
                    isActive ? "bg-purple-100 text-purple-600" : "bg-purple-50 text-purple-500"
                )}>
                    <Wrench size={18} />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="font-bold text-slate-800 text-sm">Tool Executor</div>
                    <div className="text-[10px] text-slate-400 font-medium">
                        Executes active tools
                    </div>
                </div>
            </div>

            {/* Content Area */}
            <div className="p-3 bg-slate-50/30 rounded-b-xl">
                <div className="text-xs text-slate-500 leading-relaxed">
                    Dynamically executes tools requested by the Agent and returns results.
                </div>
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
