import { create } from 'zustand';
import {
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  type Edge,
  type Node,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type NodeChange,
  type EdgeChange,
  type Connection,
  MarkerType,
} from '@xyflow/react';

type GraphState = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (node: Node) => void;
};

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],
  onNodesChange: (changes: NodeChange[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },
  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },
  onConnect: (connection: Connection) => {
    const edge = {
      ...connection,
      type: 'smoothstep',
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 20,
        height: 20,
      },
    };

    // [FEATURE] Automatic Resource Binding Visualization
    // If connecting to a 'rag' node, use the 'resource' edge type (dashed line)
    // and disable flow animation, as this represents a capability binding, not execution flow.
    const targetNode = get().nodes.find((n) => n.id === connection.target);
    if (targetNode?.type === 'rag') {
      edge.type = 'resource';
      edge.markerEnd = { type: MarkerType.ArrowClosed, width: 20, height: 20 }; // Keep marker
      // Clear animation if any default was applied (none here, but good practice)
    }

    set({
      edges: addEdge(edge, get().edges),
    });
  },
  setNodes: (nodes: Node[]) => set({ nodes }),
  setEdges: (edges: Edge[]) => set({ edges }),
  addNode: (node: Node) => set({ nodes: [...get().nodes, node] }),
}));
