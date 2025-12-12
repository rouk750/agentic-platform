import { Handle, Position, NodeProps, useReactFlow } from '@xyflow/react';
import { GitFork, Settings2, Info } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useState } from 'react';
import { useRunStore } from '../store/runStore';
import { RouterConfigDialog } from './RouterConfigDialog';
import { TechnicalInfoDialog } from './TechnicalInfoDialog';

export function RouterNode({ id, selected, data }: NodeProps) {
    const { updateNodeData } = useReactFlow();
    const activeNodeId = useRunStore((state) => state.activeNodeId);
    const isActive = id === activeNodeId;
    const [configOpen, setConfigOpen] = useState(false);
    const [infoOpen, setInfoOpen] = useState(false);

    // Ensure routes array exists
    const routes = (data.routes as any[]) || [];

    return (
        <>
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
                        <GitFork size={18} />
                    </div>

                    <div className="flex-1 min-w-0">
                        <input
                            className="font-bold text-slate-800 bg-transparent border-none p-0 focus:ring-0 w-full text-sm truncate placeholder:text-slate-400"
                            value={String(data.label || "Logic Router")}
                            onChange={(e) => updateNodeData(id, { label: e.target.value })}
                            placeholder="Router Name"
                        />
                        <div className="text-[10px] text-slate-400 font-medium">
                            {routes.length} Active Routes
                        </div>
                    </div>

                    <div className="flex items-center gap-1">
                        <button
                            onClick={() => setInfoOpen(true)}
                            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
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

                <Handle
                    type="target"
                    position={Position.Left}
                    className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white transition-transform hover:scale-125"
                />

                {/* Dynamic Output Handles */}
                <div className="py-3 space-y-3">
                    {routes.map((route, index) => (
                        <div key={route.id || index} className="relative flex justify-end items-center h-6 pr-3">
                            <div className="mr-3 text-right">
                                <div className="text-[10px] font-bold text-slate-600 truncate max-w-[120px]">
                                    {route.value ? `"${route.value}"` : `Route ${index + 1}`}
                                </div>
                                <div className="text-[8px] text-slate-400 font-mono uppercase">
                                    {route.condition}
                                </div>
                            </div>
                            <Handle
                                type="source"
                                position={Position.Right}
                                id={route.target_handle}
                                className="!w-3 !h-3 !bg-purple-500 !border-2 !border-white !-right-3 transition-transform hover:scale-125"
                            />
                        </div>
                    ))}

                    {/* Default Handle */}
                    <div className="relative flex justify-end items-center h-6 pr-3 pt-2 border-t border-slate-50 mt-1">
                        <span className="text-[10px] mr-3 text-slate-400 font-medium">Default</span>
                        <Handle
                            type="source"
                            position={Position.Right}
                            id="default"
                            className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white !-right-3 transition-transform hover:scale-125"
                        />
                    </div>
                </div>
            </div>

            <RouterConfigDialog
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
