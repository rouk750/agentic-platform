import { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useReactFlow,
  Panel,
  ReactFlowProvider,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { v4 as uuidv4 } from 'uuid';
import { toast } from 'sonner';
import { Save, Loader2, ArrowLeft } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';

import { useGraphStore } from '../store/graphStore';
import { useRunStore } from '../store/runStore';
import { flowApi } from '../api/flows';
import { AgentNode } from '../nodes/AgentNode';
import { RouterNode } from '../nodes/RouterNode';
import { ToolNode } from '../nodes/ToolNode';
import { RAGNode } from '../nodes/RAGNode';
import { SmartNode } from '../nodes/SmartNode';

import IteratorNode from '../nodes/IteratorNode';
import { SubgraphNode } from '../nodes/SubgraphNode';
import ResourceEdge from '../edges/ResourceEdge';

import { cleanNode, cleanEdge } from '../utils/flowUtils';

const nodeTypes = {
  agent: AgentNode,
  router: RouterNode,
  tool: ToolNode,
  rag: RAGNode,
  smart_node: SmartNode,
  iterator: IteratorNode,
  subgraph: SubgraphNode,
};

const edgeTypes = {
  resource: ResourceEdge,
};

function FlowEditorInstance() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, setNodes, setEdges } =
    useGraphStore();
  const { screenToFlowPosition, toObject } = useReactFlow();

  const [flowName, setFlowName] = useState('Untitled Flow');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastSavedData, setLastSavedData] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const { reset: resetRunState, activeFlowId, setActiveFlowId } = useRunStore();

  // Reset run state only if we switch to a DIFFERENT flow
  useEffect(() => {
    if (id && id !== activeFlowId) {
      resetRunState();
      setActiveFlowId(id);
    } else if (!id) {
      // If new flow (no ID), maybe reset?
      // resetRunState();
      // setActiveFlowId('new');
    }
  }, [id, resetRunState, activeFlowId, setActiveFlowId]);

  // Check for dirty state
  useEffect(() => {
    if (!loading && lastSavedData) {
      try {
        const saved = JSON.parse(lastSavedData);
        const savedNodes = saved.nodes?.map(cleanNode) || [];
        const savedEdges = saved.edges?.map(cleanEdge) || [];

        const current = toObject();
        // Ensure we handle potential undefined/nulls safely, though toObject should return arrays
        const currentNodes = current.nodes.map(cleanNode);
        const currentEdges = current.edges.map(cleanEdge);

        const isNodesChanged = JSON.stringify(savedNodes) !== JSON.stringify(currentNodes);
        const isEdgesChanged = JSON.stringify(savedEdges) !== JSON.stringify(currentEdges);

        // Check if name changed (optional, but good practice)
        // const isNameChanged = flowName !== initialFlowName; // we'd need to store initial name

        setIsDirty(isNodesChanged || isEdgesChanged);
      } catch (e) {
        console.error('Error checking dirty state', e);
      }
    }
  }, [nodes, edges, flowName, lastSavedData, toObject, loading]);

  // Warn on browser unload
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = ''; // Chrome requires returnValue to be set
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  // Load flow data if ID is present
  useEffect(() => {
    if (id && id !== 'new') {
      const loadFlow = async () => {
        try {
          setLoading(true);
          const flow = await flowApi.getOne(parseInt(id));
          setFlowName(flow.name);

          if (flow.data) {
            const parsedData = JSON.parse(flow.data);
            // Assuming saved data structure is { nodes, edges, viewport }
            if (parsedData.nodes) setNodes(parsedData.nodes);
            if (parsedData.edges) setEdges(parsedData.edges);
            // Viewport restore could be added here

            // Set initial saved data state for dirty checking
            // We need to reconstruct what toObject() would return to match exactly
            // Or better, wait for nodes/edges to be set and then take a snapshot?
            // Actually, flow.data is exactly what we saved.
            setLastSavedData(flow.data);
          }
        } catch (error: any) {
          console.error('Failed to load flow', error);
          toast.error(`Failed to load flow: ${error.message || 'Unknown error'}`);
          navigate('/');
        } finally {
          setLoading(false);
        }
      };
      loadFlow();
    } else {
      // Reset for new flow
      setNodes([]);
      setEdges([]);
      setFlowName('New Untitled Flow');
      setLoading(false);
      // Initial state for new flow
      setLastSavedData(JSON.stringify({ nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 } }));
    }
  }, [id, setNodes, setEdges, navigate]);

  // Active Edge Highlighting
  const activeNodeIds = useRunStore((state) => state.activeNodeIds);

  useEffect(() => {
    const { edges } = useGraphStore.getState();

    const newEdges = edges.map((edge) => {
      // If there's an active node, highlight edges targeting it
      const isTargetActive = activeNodeIds.includes(edge.target);

      // Refinement: Only highlight if the SOURCE node has also executed at least once (or we don't know about it e.g. START)
      // This prevents "return edges" (Tool -> Agent) from highlighting before the Tool has actually run.
      const sourceExecutionCount = useRunStore.getState().nodeExecutionCounts[edge.source] || 0;
      const isSourceReady = sourceExecutionCount > 0;

      // Special case: Edges from "START" (implicit or explicit) might not have execution counts if they are virtual.
      // But usually edges from actual nodes (like Tools) will have counts.
      // If the source node is NOT in the active list and has count 0, it definitely hasn't run.
      // But wait, "START" isn't in nodes usually.
      // We can check if source exists in `nodes`. If it does, check count. If not (e.g. system START), assume ready.
      const sourceNode = nodes.find((n) => n.id === edge.source);
      const shouldHighlight = isTargetActive && (!sourceNode || isSourceReady);

      if (shouldHighlight) {
        return {
          ...edge,
          animated: true,
          style: { ...edge.style, stroke: '#22c55e', strokeWidth: 2 },
        };
      }
      // Reset others
      return {
        ...edge,
        animated: false,
        style: { ...edge.style, stroke: '#b1b1b7', strokeWidth: 1 },
      };
    });

    // Only update if something changed (JSON stringify is a cheap deep compare for simple edge arrays)
    if (JSON.stringify(newEdges) !== JSON.stringify(edges)) {
      setEdges(newEdges);
    }
  }, [activeNodeIds, setEdges]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const dataString = event.dataTransfer.getData('application/reactflow/data');
      let data: any = { label: `New ${type}` };

      if (dataString) {
        try {
          const parsedData = JSON.parse(dataString);
          data = { ...data, ...parsedData };
        } catch (e) {
          console.error('Failed to parse drop data', e);
        }
      }

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: uuidv4(),
        type,
        position,
        data,
      };

      addNode(newNode);
    },
    [screenToFlowPosition, addNode]
  );

  const handleSave = async () => {
    if (!flowName || flowName.trim().length === 0) {
      toast.error('Please enter a flow name');
      return;
    }

    setSaving(true);
    try {
      const currentGraph = toObject(); // Gets nodes, edges, viewport

      // Clean data before saving
      const cleanGraph = {
        ...currentGraph,
        nodes: currentGraph.nodes.map(cleanNode),
        edges: currentGraph.edges.map(cleanEdge),
      };

      const dataString = JSON.stringify(cleanGraph);

      if (id && id !== 'new') {
        // Update existing
        await flowApi.update(parseInt(id), {
          name: flowName,
          data: dataString,
        });
        toast.success('Flow saved successfully');
        setLastSavedData(dataString);
        setIsDirty(false);
      } else {
        // Create new
        const newFlow = await flowApi.create({
          name: flowName,
          data: dataString,
        });
        toast.success('Flow created');
        setLastSavedData(dataString);
        setIsDirty(false);
        navigate(`/editor/${newFlow.id}`, { replace: true });
      }
    } catch (error: any) {
      console.error(error);
      toast.error(`Failed to save flow: ${error.message || 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  const handleBack = () => {
    if (isDirty) {
      if (!window.confirm('You have unsaved changes. Are you sure you want to leave?')) {
        return;
      }
    }
    navigate('/');
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-2 text-slate-500">
          <Loader2 className="animate-spin text-blue-600" size={32} />
          <span>Loading flow...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-slate-50 relative">
      {/* Header Overlay */}
      <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-start pointer-events-none">
        <div className="pointer-events-auto">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg shadow-sm hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft size={16} /> Back
          </button>
        </div>

        <Panel position="top-right" className="!m-0 pointer-events-auto flex gap-2">
          <div className="bg-white/90 backdrop-blur px-4 py-2 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
            <input
              value={flowName}
              onChange={(e) => setFlowName(e.target.value)}
              className="font-semibold text-slate-700 bg-transparent border border-transparent hover:border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded px-1 -ml-1 transition-all outline-none w-48"
              placeholder="Flow Name"
            />
            <div className="h-4 w-px bg-slate-200"></div>
            <button
              onClick={handleSave}
              disabled={saving}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors text-sm font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed ${isDirty ? 'bg-amber-600 hover:bg-amber-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              {saving ? 'Saving...' : isDirty ? 'Save*' : 'Save'}
            </button>
          </div>
        </Panel>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onDragOver={onDragOver}
        onDrop={onDrop}
        fitView
        defaultEdgeOptions={{
          type: 'smoothstep',
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
          },
        }}
      >
        <Background gap={20} color="#e2e8f0" />
        <Controls className="bg-white border-slate-200 shadow-md text-slate-600" />
        <MiniMap
          className="border-slate-200 shadow-lg rounded-lg overflow-hidden"
          nodeColor={(node) => {
            switch (node.type) {
              case 'agent':
                return '#3b82f6';
              case 'tool':
                return '#f97316';
              case 'router':
                return '#a855f7';
              default:
                return '#64748b';
            }
          }}
        />
      </ReactFlow>
    </div>
  );
}

export default function FlowEditor() {
  return (
    <ReactFlowProvider>
      <FlowEditorInstance />
    </ReactFlowProvider>
  );
}
