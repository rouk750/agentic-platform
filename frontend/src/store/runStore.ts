import { create } from 'zustand';
import type { Message, LogEntry } from '../types/execution';

interface RunState {
  status: 'idle' | 'connecting' | 'running' | 'paused' | 'error' | 'done';
  messages: Message[];
  activeNodeIds: string[];
  pausedNodeId: string | null; // HITL
  nodeLabels: Record<string, string>; // Map nodeId -> Label
  currentToolName: string | null;
  iteratorProgress: Record<string, { current: number; total: number }>;
  nodeExecutionCounts: Record<string, number>;
  toolStats: Record<string, Record<string, number>>; // nodeId -> toolName -> count
  logs: LogEntry[];
  
  // Actions
  setStatus: (status: RunState['status']) => void;
  setPaused: (nodeId: string | null) => void;
  addActiveNode: (nodeId: string) => void;
  removeActiveNode: (nodeId: string) => void;
  setNodeLabels: (labels: Record<string, string>) => void;
  setCurrentTool: (toolName: string | null) => void;
  incrementNodeExecution: (nodeId: string) => void;
  addToolExecution: (nodeId: string, toolName: string) => void;
  updateIteratorProgress: (nodeId: string, current: number, total: number) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  appendToken: (token: string) => void;
  addLog: (entry: Omit<LogEntry, 'timestamp'>) => void;
  clearSession: () => void;
  reset: () => void;
}

export const useRunStore = create<RunState>((set) => ({
  status: 'idle',
  messages: [],
  activeNodeIds: [],
  pausedNodeId: null,
  nodeLabels: {},
  currentToolName: null,
  nodeExecutionCounts: {}, 
  toolStats: {},
  iteratorProgress: {},
  logs: [],

  setStatus: (status) => set({ status }),
  setPaused: (pausedNodeId) => set({ status: pausedNodeId ? 'paused' : 'running', pausedNodeId }),
  
  addActiveNode: (nodeId) => set((state) => {
    if (state.activeNodeIds.includes(nodeId)) return state;
    return { activeNodeIds: [...state.activeNodeIds, nodeId] };
  }),

  removeActiveNode: (nodeId) => set((state) => ({
    activeNodeIds: state.activeNodeIds.filter(id => id !== nodeId)
  })),
  
  setNodeLabels: (nodeLabels) => set({ nodeLabels }),

  setCurrentTool: (currentToolName) => set({ currentToolName }),

  incrementNodeExecution: (nodeId) => set((state) => ({
    nodeExecutionCounts: {
      ...state.nodeExecutionCounts,
      [nodeId]: (state.nodeExecutionCounts[nodeId] || 0) + 1
    }
  })),

  addToolExecution: (nodeId, toolName) => set((state) => {
    const nodeStats = state.toolStats[nodeId] || {};
    const currentCount = nodeStats[toolName] || 0;
    return {
        toolStats: {
            ...state.toolStats,
            [nodeId]: {
                ...nodeStats,
                [toolName]: currentCount + 1
            }
        }
    };
  }),

  updateIteratorProgress: (nodeId, current, total) => set((state) => ({ // Implemented
    iteratorProgress: {
      ...state.iteratorProgress,
      [nodeId]: { current, total }
    }
  })),
  
  addMessage: (msg) => set((state) => ({
    messages: [
      ...state.messages,
      {
        ...msg,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      },
    ],
  })),
  
  appendToken: (token) => set((state) => {
    const messages = [...state.messages];
    const lastMsg = messages[messages.length - 1];
    
    // Check if the last message is from AI AND matches ONE OF the current active nodes
    // Ideally we track which node is emitting the token, but usually token events don't carry nodeId. 
    // Assuming backend sends serialized updates, usually one stream at a time or we just append to last AI msg.
    // For robust parallel streaming, we'd need nodeId in token event. 
    // Current logic: if last msg is AI, append.
    
    // We relax the nodeId check slightly or rely on the fact that usually only LLMs stream tokens.
    // However, if two LLMs stream at once, this will interleave. 
    // Standard solution: token event should have nodeId. 
    // For now, we'll just check if role is 'ai'.
    
    const isAiMsg = lastMsg && lastMsg.role === 'ai';

    if (isAiMsg) {
        const updatedMsg = { ...lastMsg, content: lastMsg.content + token };
        messages[messages.length - 1] = updatedMsg;
        return { messages };
    } else {
        // Warning: This might pick a random sender if multiple nodes are active.
        // We'll trust the single-stream assumption for now or pick the last added node.
        const lastActiveNode = state.activeNodeIds[state.activeNodeIds.length - 1];
        const senderName = lastActiveNode ? state.nodeLabels[lastActiveNode] : undefined;
        return {
            messages: [
                ...messages,
                {
                    id: crypto.randomUUID(),
                    role: 'ai',
                    content: token,
                    name: senderName,
                    nodeId: lastActiveNode,
                    timestamp: Date.now()
                }
            ]
        };
    }
  }),
  
  addLog: (entry) => set((state) => ({
    logs: [...state.logs, { ...entry, timestamp: Date.now() }]
  })),
  
  clearSession: () => set({
    status: 'idle',
    messages: [],
    activeNodeIds: [],
    nodeExecutionCounts: {},
    toolStats: {},
    logs: []
  }),

  reset: () => set({
    status: 'idle',
    messages: [],
    activeNodeIds: [],
    currentToolName: null,
    iteratorProgress: {},
    nodeExecutionCounts: {},
    toolStats: {},
    logs: []
  }),
}));
