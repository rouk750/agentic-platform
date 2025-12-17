import { useState, useRef, useEffect } from 'react';
import { useRunStore } from '../../store/runStore';
import { useAgentRuntime } from '../../hooks/useAgentRuntime';
import { ChatMessage } from './ChatMessage';
import { Play, Square, Eraser, Loader2, Eye, EyeOff } from 'lucide-react';
import { useGraphStore } from '../../store/graphStore';
import clsx from 'clsx';
// Wait, I need to check where useGraphStore is. Assuming standard path.

export function ChatPanel() {
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    const { messages, status, clearSession, pausedNodeId, nodeLabels } = useRunStore();
    const { connect, stop, resume } = useAgentRuntime();

    // Actually, useGraphStore likely stores nodes/edges.
    // I need to confirm how to get the graph layout to send to backend.
    // Assuming `useGraphStore` has `nodes` and `edges` and I can structure it.
    const nodes = useGraphStore((state) => state.nodes);
    const edges = useGraphStore((state) => state.edges);

    useEffect(() => {
        // Auto-scroll
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleRun = () => {
        if (!input.trim() && messages.length === 0) return;

        if (status === 'running') {
            stop();
            return;
        }

        // Construct graph payload
        const graphJson = { nodes, edges };
        const prompt = input || "Start"; // Default prompt if re-running without input?

        connect(graphJson, prompt);
        setInput('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleRun();
        }
    };

    const [width, setWidth] = useState(384); // Default 96 * 4 = 384px
    const [isResizing, setIsResizing] = useState(false);
    const [showTraces, setShowTraces] = useState(true);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            // ... (existing resize logic skipped for brevity in replace block if possible, but I need to be careful with context)
            // Actually, I can just insert the state at the top and the button in the header in one go if I include enough context, 
            // or split it. Splitting is safer. 
            // Let's just add the state first.
            // Calculate new width: Window Width - Mouse X
            // Adding a min-width constraint (e.g., 300px) and max-width (e.g., 800px)
            const newWidth = document.body.clientWidth - e.clientX;
            if (newWidth > 300 && newWidth < 800) {
                setWidth(newWidth);
            }
        };

        const handleMouseUp = () => {
            setIsResizing(false);
            document.body.style.cursor = 'default';
        };

        if (isResizing) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'default';
        };
    }, [isResizing]);

    const startResizing = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    };

    const isRunning = status === 'running' || status === 'connecting';

    return (
        <div
            style={{ width: `${width}px` }}
            className="flex flex-col h-full bg-zinc-50 dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 shadow-xl z-10 transition-none relative"
        >
            {/* Drag Handle */}
            <div
                onMouseDown={startResizing}
                className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-400/50 transition-colors z-50 transform -translate-x-1/2"
                title="Drag to resize"
            />

            {/* Header */}
            <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-white dark:bg-zinc-900 h-14">
                <div className="flex items-center gap-3 min-w-0 flex-1 mr-2">
                    <h2 className="font-semibold text-zinc-800 dark:text-zinc-200 shrink-0">Execution</h2>

                    {/* Active Node Indicator in Header */}
                    {status === 'running' && useRunStore.getState().activeNodeId && (
                        <div className="flex items-center gap-2 px-2 py-1 bg-blue-50 dark:bg-blue-900/40 rounded-full border border-blue-100 dark:border-blue-800/50 min-w-0 animate-in fade-in zoom-in duration-200">
                            <Loader2 size={12} className="animate-spin text-blue-600 dark:text-blue-400 shrink-0" />
                            <span className="text-[10px] font-medium text-blue-700 dark:text-blue-300 truncate max-w-[150px]">
                                {useRunStore.getState().nodeLabels[useRunStore.getState().activeNodeId!] || useRunStore.getState().activeNodeId}
                            </span>
                            <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 border-l border-blue-200 dark:border-blue-700 pl-2 shrink-0">
                                #{useRunStore.getState().nodeExecutionCounts[useRunStore.getState().activeNodeId!] || 1}
                            </span>
                        </div>
                    )}
                </div>

                <div className="flex gap-2 shrink-0">
                    <button
                        onClick={() => setShowTraces(!showTraces)}
                        className={clsx(
                            "p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md transition-colors",
                            showTraces ? "text-indigo-600 dark:text-indigo-400" : "text-zinc-500"
                        )}
                        title={showTraces ? "Hide Traces" : "Show Traces"}
                    >
                        {showTraces ? <Eye size={18} /> : <EyeOff size={18} />}
                    </button>

                    <button
                        onClick={clearSession}
                        className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md text-zinc-500"
                        title="Clear Session"
                        disabled={isRunning}
                    >
                        <Eraser size={18} />
                    </button>
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
                {messages.length === 0 && (
                    <div className="text-center text-zinc-400 mt-20 text-sm">
                        Ready to run. <br /> Enter a message to start the agent.
                    </div>
                )}

                {messages
                    .filter(msg => showTraces || msg.role !== 'trace')
                    .map((msg) => (
                        <ChatMessage key={msg.id} message={msg} />
                    ))}
                {status === 'connecting' && (
                    <div className="flex items-center gap-2 text-zinc-500 text-sm animate-pulse">
                        <Loader2 size={14} className="animate-spin" /> Connecting...
                    </div>
                )}
            </div>

            {/* Paused/Resume Banner */}
            {status === 'paused' && pausedNodeId && (
                <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border-t border-orange-200 dark:border-orange-800 flex items-center justify-between animate-in slide-in-from-bottom-2">
                    <div className="flex flex-col">
                        <span className="text-xs font-bold text-orange-600 dark:text-orange-400 uppercase tracking-wider">Waiting for Approval</span>
                        <span className="text-sm font-medium text-orange-800 dark:text-orange-200">
                            Paused at {nodeLabels[pausedNodeId] || pausedNodeId}
                        </span>
                    </div>
                    <button
                        onClick={resume}
                        className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg shadow-sm transition-colors font-medium text-sm"
                    >
                        <Play size={16} fill="currentColor" /> Resume
                    </button>
                </div>
            )}

            {/* Input Area */}
            <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
                <div className="relative">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your instruction..."
                        className="w-full bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none h-24 text-sm"
                        disabled={isRunning}
                    />
                    <button
                        onClick={handleRun}
                        disabled={!input.trim() && messages.length === 0 && !isRunning}
                        className={clsx(
                            "absolute bottom-3 right-3 p-2 rounded-lg transition-colors",
                            isRunning
                                ? "bg-red-500 hover:bg-red-600 text-white"
                                : "bg-blue-600 hover:bg-blue-700 text-white"
                        )}
                    >
                        {isRunning ? <Square size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
                    </button>
                </div>
            </div>
        </div>
    );
}
