import { Clock, CheckCircle2, AlertCircle, CircleDashed } from "lucide-react";

interface TimelineProps {
    steps: any[];
    selectedId: string | null;
    onSelect: (id: string) => void;
}

export default function ExecutionTimeline({ steps, selectedId, onSelect }: TimelineProps) {
    return (
        <div className="h-full flex flex-col">
            <div className="p-3 border-b border-slate-100 bg-slate-50/50">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Timeline</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {steps.length === 0 && (
                    <div className="text-center py-8 text-slate-400 text-sm">
                        Waiting for events...
                    </div>
                )}

                {steps.map((step) => {
                    const isSelected = selectedId === step.node_id;
                    const date = new Date(step.created_at);
                    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

                    return (
                        <div
                            key={step.node_id + step.created_at} // Composite key in case of duplicates
                            onClick={() => onSelect(step.node_id)}
                            className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected
                                ? "bg-blue-50 border-blue-200 ring-1 ring-blue-200"
                                : "bg-white border-slate-200 hover:border-blue-300"
                                }`}
                        >
                            <div className="flex items-start gap-3">
                                <div className="mt-0.5 text-green-500">
                                    <CheckCircle2 size={16} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-center mb-1">
                                        <div className="flex items-center gap-2 overflow-hidden">
                                            <span className="font-medium text-sm text-slate-800 truncate" title={step.node_id}>
                                                {step.label || step.node_id}
                                            </span>
                                            {step.label && step.label !== step.node_id && (
                                                <span className="text-[10px] text-zinc-400 font-mono truncate max-w-[80px]">
                                                    {step.node_id.slice(0, 8)}...
                                                </span>
                                            )}
                                        </div>
                                        <span className="text-[10px] text-slate-400 font-mono shrink-0 ml-2">{timeStr}</span>
                                    </div>
                                    <div className="text-xs text-slate-500 truncate font-mono bg-slate-50 px-1 py-0.5 rounded border border-slate-100 mb-1">
                                        {/* Show part of state as preview, e.g. last message */}
                                        {step.state?.messages ? `${Object.values(step.state.messages).length} messages` : 'No messages'}
                                    </div>
                                    <div className="mt-1 flex gap-2">
                                        {step.duration && (
                                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-slate-100 rounded text-[10px] text-slate-600 font-mono">
                                                <Clock size={10} /> {step.duration}s
                                            </span>
                                        )}
                                        {step.tokens && (
                                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-slate-100 rounded text-[10px] text-slate-600 font-mono">
                                                {step.tokens} tok
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
