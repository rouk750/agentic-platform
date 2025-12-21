import { create } from 'zustand';
import type { Message, LogEntry } from '../types/execution';
import { findTargetMessageIndex } from '../utils/executionUtils';

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
  appendToken: (token: string, nodeId?: string) => void;
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
  
  appendToken: (token, nodeId) => set((state) => {
    const messages = [...state.messages];
    
    // 1. Try to find an existing message to merge into (Backwards search)
    const targetIndex = findTargetMessageIndex(messages, nodeId);

    if (targetIndex !== -1) {
        // Found a matching message in the current turn
        const targetMsg = messages[targetIndex];
        const updatedMsg = { ...targetMsg, content: targetMsg.content + token };
        messages[targetIndex] = updatedMsg;
        return { messages };
    }
    
    // 2. Fallback: If no nodeId or no match found
    // Check if the VERY LAST message is "appendable" (AI role, no specific ID conflict)
    // This handles the legacy case or "blind append"
    const lastMsg = messages[messages.length - 1];
    const isAiMsg = lastMsg && lastMsg.role === 'ai';
    
    // Only append blindly if we have NO nodeId to conflict with
    const canBlindAppend = isAiMsg && !nodeId && !lastMsg.nodeId; 

    if (canBlindAppend) {
         const updatedMsg = { ...lastMsg, content: lastMsg.content + token };
         messages[messages.length - 1] = updatedMsg;
         return { messages };
    }

    // 3. Create New Bubble
    // If we don't have a nodeId, we fall back to the last active one (risky but better than nothing)
    const effectiveNodeId = nodeId || state.activeNodeIds[state.activeNodeIds.length - 1];
    const effectiveName = effectiveNodeId ? (state.nodeLabels[effectiveNodeId] || effectiveNodeId) : undefined;
    
    return {
        messages: [
            ...messages,
            {
                id: crypto.randomUUID(),
                role: 'ai',
                content: token,
                name: effectiveName,
                nodeId: effectiveNodeId,
                timestamp: Date.now()
            }
        ]
    };
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
