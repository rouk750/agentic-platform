import { Handle, Position, useReactFlow, type NodeProps, type Node } from '@xyflow/react';
import { Workflow } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useRunStore } from '../store/runStore';
import { flowApi, type Flow } from '../api/flows';
import { toast } from 'sonner';

export type SubgraphNodeData = {
    label: string;
    flow_id?: string;
};

type SubgraphNodeType = Node<SubgraphNodeData>;

export function SubgraphNode({ id, data, selected }: NodeProps<SubgraphNodeType>) {
    const { id: currentFlowId } = useParams();
    const { updateNodeData } = useReactFlow();
    const activeNodeId = useRunStore((state) => state.activeNodeId);
    const isActive = id === activeNodeId;

    // Local state for list of flows
    const [flows, setFlows] = useState<Flow[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const f = await flowApi.getAll();
                // Filter out current flow to avoid direct recursion
                const validFlows = currentFlowId ? f.filter(flow => flow.id?.toString() !== currentFlowId) : f;
                setFlows(validFlows);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [currentFlowId]);

    return (
        <div
            className={twMerge(
                'bg-white border-2 rounded-xl w-64 shadow-sm transition-all duration-300 group',
                selected ? 'border-purple-500 ring-2 ring-purple-500/20 shadow-md' : 'border-slate-200 hover:border-slate-300',
                isActive && 'border-green-500 ring-4 ring-green-500/20 shadow-xl scale-105'
            )}
        >
            {/* Header */}
            <div className="flex items-center gap-3 p-3 border-b border-slate-100 bg-gradient-to-b from-white to-purple-50/50 rounded-t-xl">
                <div className={twMerge(
                    "p-2 rounded-lg transition-colors flex items-center justify-center relative",
                    isActive ? "bg-green-100 text-green-600" : "bg-purple-100 text-purple-600"
                )}>
                    <Workflow size={18} />
                </div>

                <div className="flex-1 min-w-0">
                    <input
                        className="font-bold text-slate-800 bg-transparent border-none p-0 focus:ring-0 w-full text-sm truncate placeholder:text-slate-400"
                        value={String(data.label)}
                        onChange={(e) => updateNodeData(id, { label: e.target.value })}
                        placeholder="Subgraph Name"
                    />
                    <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1 mt-0.5">
                        <span className="truncate max-w-[120px]">
                            {data.flow_id
                                ? flows.find(f => f.id?.toString() === data.flow_id)?.name || `Flow #${data.flow_id} `
                                : "Select a Flow"
                            }
                        </span>
                    </div>
                </div>
            </div>

            {/* Body */}
            <div className="p-3">
                <select
                    className="w-full text-xs p-1.5 rounded border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                    value={data.flow_id || ""}
                    onChange={(e) => updateNodeData(id, { flow_id: e.target.value })}
                >
                    <option value="" disabled>Select Flow to Run</option>
                    {flows.map(f => (
                        <option key={f.id} value={f.id?.toString()}>{f.name}</option>
                    ))}
                </select>
            </div>

            {/* Handles */}
            <div className="absolute -left-3 top-1/2 -translate-y-1/2 flex items-center">
                <Handle
                    type="target"
                    position={Position.Left}
                    className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white transition-transform hover:scale-125"
                />
            </div>

            <div className="absolute -right-3 top-1/2 -translate-y-1/2 flex items-center">
                <Handle
                    type="source"
                    position={Position.Right}
                    className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white transition-transform hover:scale-125"
                />
            </div>
        </div>
    );
}
