import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps, useReactFlow } from '@xyflow/react';
import { RefreshCw, Settings2 } from 'lucide-react';
import { IteratorConfigDialog } from './IteratorConfigDialog';

const IteratorNode = memo(({ id, data, isConnectable }: NodeProps) => {
    const [configOpen, setConfigOpen] = useState(false);
    const { updateNodeData } = useReactFlow();

    return (
        <>
            <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-orange-500 w-64 relative h-[150px] flex flex-col justify-between">
                {/* Input Handle */}
                <Handle
                    type="target"
                    position={Position.Left}
                    isConnectable={isConnectable}
                    className="w-3 h-3 bg-gray-400"
                />

                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <div className="rounded-full w-10 h-10 flex justify-center items-center bg-orange-100 text-orange-600 mr-3">
                            <RefreshCw size={20} />
                        </div>
                        <div>
                            <div className="text-md font-bold text-gray-700">{String(data.label || 'Iterator')}</div>
                            <div className="text-xs text-gray-500">Iterates over {String(data.input_list_variable || 'items')}</div>
                        </div>
                    </div>

                    <button
                        onClick={() => setConfigOpen(true)}
                        className="nodrag p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors z-50 cursor-pointer"
                    >
                        <Settings2 size={18} />
                    </button>
                </div>

                <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-400 text-center">
                    Next Item &rarr; {String(data.output_item_variable || 'current_item')}
                </div>

                {/* Output Handles */}

                {/* 1. Next Item Output (Right - Middle) */}
                <div className="absolute right-0 top-[50%] flex items-center pr-2" style={{ transform: 'translateY(-50%)' }}>
                    <div className="text-[10px] text-gray-500 mr-1 bg-white px-1 border-gray-100 border rounded absolute right-4 whitespace-nowrap">Next Item</div>
                </div>
                <Handle
                    type="source"
                    position={Position.Right}
                    id="next"
                    style={{ top: '50%', background: '#f97316' }}
                    isConnectable={isConnectable}
                    className="w-3 h-3"
                />

                {/* 2. Complete Output (Right - Bottom) */}
                <div className="absolute right-0 bottom-4 flex items-center pr-2">
                    <div className="text-[10px] text-gray-500 mr-1 bg-white px-1 border-gray-100 border rounded absolute right-4 whitespace-nowrap">Complete</div>
                </div>
                <Handle
                    type="source"
                    position={Position.Right}
                    id="complete"
                    style={{ top: '85%', background: '#22c55e' }}
                    isConnectable={isConnectable}
                    className="w-3 h-3"
                />
            </div>

            <IteratorConfigDialog
                open={configOpen}
                onOpenChange={setConfigOpen}
                data={data}
                onUpdate={(updates) => updateNodeData(id, updates)}
            />
        </>
    );
});

export default IteratorNode;
