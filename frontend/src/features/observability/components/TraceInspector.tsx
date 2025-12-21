import { Code2, ArrowRightLeft, Database } from "lucide-react";

interface InspectorProps {
    stepId: string | null;
    data: any | null; // StepSnapshot
}

export default function TraceInspector({ stepId, data }: InspectorProps) {
    if (!stepId) {
        return (
            <div className="h-full flex items-center justify-center text-slate-400">
                <p>Select a step to inspect details</p>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            <div className="p-3 border-b border-slate-200 bg-white flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-700">Trace Details: {stepId}</h3>
                <div className="flex gap-1">
                    <button className="p-1.5 hover:bg-slate-100 rounded text-slate-500" title="State Diff">
                        <ArrowRightLeft size={16} />
                    </button>
                    <button className="p-1.5 hover:bg-slate-100 rounded text-slate-500 bg-slate-100 text-blue-600" title="Raw JSON">
                        <Code2 size={16} />
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">

                {/* State Snapshot */}
                <section>
                    <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-2">
                        <Database size={12} />
                        Full State Snapshot
                    </h4>
                    <div className="bg-slate-50 rounded-lg border border-slate-200 p-3 font-mono text-xs text-slate-600 overflow-x-auto">
                        <pre>{JSON.stringify(data?.state || {}, null, 2)}</pre>
                    </div>
                </section>

                {/* Raw Data (Debug) */}
                <section>
                    <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-2">
                        <code className="bg-slate-100 px-1 rounded">DEBUG</code> Raw Frame
                    </h4>
                    <div className="bg-slate-50 rounded-lg border border-slate-200 p-3 font-mono text-xs text-slate-400 overflow-x-auto">
                        <pre>{JSON.stringify(data || {}, null, 2)}</pre>
                    </div>
                </section>

            </div>
        </div>
    );
}
