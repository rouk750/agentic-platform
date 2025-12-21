import { Play, Sparkles, TerminalSquare, Square } from "lucide-react";
import { useIsolatedRuntime } from "../../../hooks/useIsolatedRuntime";
import { useRunStore } from "../../../store/runStore";
import { useState } from "react";

interface PlaygroundProps {
    stepId: string | null;
    data: any | null; // StepSnapshot
}

export default function PromptPlayground({ stepId, data }: PlaygroundProps) {
    // Extract last message or context to prefill simulated input
    const messages = data?.state?.messages || [];
    const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
    const initialInput = lastMessage ? `${lastMessage.role}: ${lastMessage.content}` : "User: ..."; // Simplified

    // Extract system prompt from state if available (conceptually)
    // For now we don't have explicit system prompt in snapshot unless we store it.
    // Let's use a placeholder or try to find a 'SystemMessage' in messages.
    const systemMsg = messages.find((m: any) => m.role === 'system');
    const systemPrompt = systemMsg ? systemMsg.content : "System prompt not found in trace history.";

    const [input, setInput] = useState("");
    const { runNode, stop, output, status, logs } = useIsolatedRuntime();
    const { graphDefinition } = useRunStore();

    // Fallback: update local input state when derived initialInput changes (only on mount/step change)
    if (input === "" && initialInput) {
        // This is a bit risky in render, usually useEffect.
        // Let's rely on defaultValue for initial and onChange for state.
    }

    const handleRun = () => {
        // We need the graph structure. 
        // Ideally we fetch it from store or parent.
        // For now, let's assume `data.config` has graph or we reconstruct it.
        // Actually, snapshots usually don't have the full graph definition.
        // We might need to pass graph from parent or fetch it.
        // WORKAROUND: We assume the MAIN graph is what we want to test.
        // We can get it from useRunStore? No, store has state, not definition (unless we added it).
        // Let's try to get it from `useGraphStore` if available?
        // Or assume the parent page has it.

        // For this Prototype phase: We will just log "Running..." 
        // and ideally we need to fix the graph source.

        // Assuming we can get current graph from useGraphStore (if it's loaded in editor)
        // But Debug page might be standalone.
        // Let's try to grab it from LocalStorage or similar if we are lucky?
        // OR: Just Alert that "Graph Definition Missing" if we can't find it.

        // Let's use a dummy graph for now? No that's useless.
        // Best bet: The `data` snapshot implies we have access to the runtime state.
        // Maybe we just send the input and rely on the backend to use the *active* version?
        // That's risky if backend context is lost.

        // Wait, `data.config` usually has the compiled graph or checkpointer config, not the JSON.

        // Let's implement the UI and hook first.
        const effectiveInput = input || initialInput;

        if (!graphDefinition) {
            alert("No active graph definition found. Please run the flow once to capture it.");
            return;
        }

        // --- ISOLATION LOGIC ---
        // To run ONLY this node, we treat it as the new Entry Point.
        // We clone the graph and force 'isStart' on this node.
        const isolatedGraph = JSON.parse(JSON.stringify(graphDefinition));
        const targetNodeId = stepId || data?.node_id;

        if (isolatedGraph.nodes) {
            let found = false;
            isolatedGraph.nodes = isolatedGraph.nodes.map((node: any) => {
                if (node.id === targetNodeId) {
                    found = true;
                    return { ...node, data: { ...node.data, isStart: true } };
                }
                // Remove isStart from all others
                return { ...node, data: { ...node.data, isStart: false } };
            });

            if (!found) {
                console.warn(`Target node ${targetNodeId} not found in graph definition.`);
            }
        }

        runNode(targetNodeId || "unknown", isolatedGraph, effectiveInput);
    };

    if (!stepId) {
        return (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm text-center px-6">
                <p>Select an Agent step to enable the Playground</p>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-slate-50/30">
            <div className="p-3 border-b border-slate-200 bg-white flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <Sparkles size={16} className="text-amber-500" />
                    Prompt Playground
                </h3>
            </div>

            <div className="flex-1 p-4 space-y-4">
                {/* System Prompt (Read-Only but Copyable) */}
                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">System Prompt (Active)</label>
                    <textarea
                        className="w-full h-32 px-3 py-2 text-xs font-mono bg-slate-100 border border-slate-200 rounded-lg focus:outline-none resize-none text-slate-600"
                        readOnly
                        value={systemPrompt}
                    />
                </div>

                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">Simulated Input</label>
                    <textarea
                        className="w-full h-24 px-3 py-2 text-xs font-mono bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-800"
                        defaultValue={initialInput}
                        key={stepId} // Force re-render
                        onChange={(e) => setInput(e.target.value)}
                    />
                </div>

                <div className="space-y-2">
                    <div className="flex gap-2">
                        <button
                            onClick={handleRun}
                            disabled={status === 'running'}
                            className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center justify-center gap-2 text-sm font-medium transition-colors shadow-sm disabled:opacity-50"
                        >
                            {status === 'running' ? <Sparkles className="animate-spin" size={16} /> : <Play size={16} fill="currentColor" />}
                            {status === 'running' ? 'Running...' : 'Run Isolated Test'}
                        </button>

                        {status === 'running' && (
                            <button
                                onClick={stop}
                                className="px-3 py-2 bg-red-100 hover:bg-red-200 text-red-600 rounded-lg flex items-center justify-center transition-colors"
                                title="Stop Execution"
                            >
                                <Square size={16} fill="currentColor" />
                            </button>
                        )}
                    </div>

                    {/* Output Area (Console) */}
                    {(output || logs.length > 0) && (
                        <div className="bg-slate-900 rounded-lg p-3 text-xs font-mono text-slate-300 overflow-x-auto max-h-40 border border-slate-800">
                            <div className="flex items-center gap-2 mb-2 text-slate-500 border-b border-slate-700 pb-1">
                                <TerminalSquare size={12} />
                                <span>Output Console</span>
                            </div>
                            {logs.map((log, i) => (
                                <div key={i} className="text-slate-500">{log}</div>
                            ))}
                            {output && (
                                <div className="mt-2 text-green-400 whitespace-pre-wrap">{JSON.stringify(output, null, 2)}</div>
                            )}
                        </div>
                    )}
                </div>

                <p className="text-[10px] text-slate-400 text-center">
                    Runs this node in isolation using the current graph context.
                </p>
            </div>
        </div>
    );
}
