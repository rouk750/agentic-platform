import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { useRunStore } from '../../store/runStore';
import { ArrowLeft, Play, RefreshCw, Trash2 } from 'lucide-react';

import ExecutionTimeline from './components/ExecutionTimeline';
import TraceInspector from './components/TraceInspector';
import PromptPlayground from './components/PromptPlayground';

interface StepSnapshot {
  id: string; // Unique UI ID
  node_id: string; // Backend Node ID
  state: any;
  created_at: string;
  duration?: number;
  tokens?: number;
  status: 'success' | 'error' | 'pending';
  label?: string;
}

export default function DeepObservabilityPage() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  // TODO: Fetch run history based on runId
  // For now we might rely on the store if it persists, or implement a fetcher.
  // Assuming runStore holds the active session.

  // Subscribe to store updates
  const { nodeSnapshots, clearSnapshots, nodeLabels, tokenUsage } = useRunStore();

  // Transform snapshots to Timeline Steps
  const [steps, setSteps] = useState<StepSnapshot[]>([]);

  useEffect(() => {
    // Flatten the dict of lists into a single chronological list
    const allSnapshots: StepSnapshot[] = [];

    Object.entries(nodeSnapshots).forEach(([nodeId, snapshots]) => {
      snapshots.forEach((snap: any, index: number) => {
        allSnapshots.push({
          id: `${nodeId}-${snap.created_at || Date.now()}-${index}`, // Unique ID
          node_id: nodeId,
          state: snap.state,
          created_at: snap.created_at || new Date().toISOString(),
          status: 'success',
          label: nodeLabels[nodeId] || nodeId,
          tokens: snap._meta?.tokens?.total,
          // Use config for extra metadata if needed
        });
      });
    });

    // Sort by timestamp (approximate if strings, precise if Date objects)
    // Ideally backend sends timestamp. For now created_at is likely string from ISO format.
    allSnapshots.sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    setSteps(allSnapshots);
  }, [nodeSnapshots]);

  // Find the selected snapshot data
  const selectedSnapshot = steps.find((s) => s.id === selectedStepId) || null;
  // Ideally selectedStepId should be 'nodeId-timestamp' or index.
  // For now let's assume unique node execution (which is FALSE for loops).
  // Better: Timeline passes the actual SNAPSHOT object or a unique ID.
  // Let's rely on index or modify Timeline to return the object.

  // Pass FULL snapshot data to Inspector
  const inspectorData = selectedSnapshot ? selectedSnapshot : null;

  return (
    <div className="h-screen w-full flex flex-col bg-slate-50">
      {/* Header */}
      <header className="h-14 border-b border-slate-200 bg-white px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="font-semibold text-slate-800">Deep Observability Console</h1>
            <p className="text-xs text-slate-500 font-mono">Run ID: {runId}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded font-medium border border-green-200">
            Live Connection
          </div>
          <button
            onClick={clearSnapshots}
            className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 hover:text-red-600 transition-colors"
            title="Clear History"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </header>

      {/* 3-Pane Layout */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal">
          {/* LEFT: Timeline */}
          <Panel defaultSize={20} minSize={15} className="bg-white border-r border-slate-200">
            <ExecutionTimeline
              steps={steps}
              selectedId={selectedStepId}
              onSelect={setSelectedStepId}
            />
          </Panel>

          <PanelResizeHandle className="w-1 bg-slate-100 hover:bg-blue-500 transition-colors cursor-col-resize" />

          {/* MIDDLE: Inspector */}
          <Panel defaultSize={50} minSize={30} className="bg-slate-50">
            <TraceInspector stepId={selectedStepId} data={inspectorData} />
          </Panel>

          <PanelResizeHandle className="w-1 bg-slate-100 hover:bg-blue-500 transition-colors cursor-col-resize" />

          {/* RIGHT: Playground */}
          <Panel defaultSize={30} minSize={20} className="bg-white border-l border-slate-200">
            <PromptPlayground stepId={selectedStepId} data={inspectorData} />
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}
