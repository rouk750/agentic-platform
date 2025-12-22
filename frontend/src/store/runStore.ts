import { create } from 'zustand';
import type { Message, LogEntry } from '../types/execution';
import { findTargetMessageIndex } from '../utils/executionUtils';

interface RunState {
  runId: string | null;
  activeFlowId: string | null;
  status: 'idle' | 'connecting' | 'running' | 'paused' | 'error' | 'done';
  messages: Message[];
  activeNodeIds: string[];
  pausedNodeId: string | null; // HITL
  nodeLabels: Record<string, string>; // Map nodeId -> Label
  currentToolName: string | null;
  iteratorProgress: Record<string, { current: number; total: number }>;
  nodeExecutionCounts: Record<string, number>;
  toolStats: Record<string, Record<string, number>>; // nodeId -> toolName -> count
  tokenUsage: Record<string, { input: number; output: number; total: number }>;
  pendingStepTokens: Record<string, { input: number; output: number; total: number }>; // Transient for current step
  nodeSnapshots: Record<string, any[]>; // nodeId -> list of snapshots
  graphDefinition: any | null; // For debug/replay
  logs: LogEntry[];
  
  // Actions
  setRunId: (id: string | null) => void;
  setActiveFlowId: (id: string | null) => void;
  setStatus: (status: RunState['status']) => void;
  setPaused: (nodeId: string | null) => void;
  addActiveNode: (nodeId: string) => void;
  removeActiveNode: (nodeId: string) => void;
  setNodeLabels: (labels: Record<string, string>) => void;
  setCurrentTool: (toolName: string | null) => void;
  incrementNodeExecution: (nodeId: string) => void;
  addToolExecution: (nodeId: string, toolName: string) => void;
  addTokenUsage: (nodeId: string, usage: { input_tokens: number; output_tokens: number; total_tokens: number }) => void;
  updateIteratorProgress: (nodeId: string, current: number, total: number) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  appendToken: (token: string, nodeId?: string) => void;
  addLog: (entry: Omit<LogEntry, 'timestamp'>) => void;
  addSnapshot: (nodeId: string, snapshot: any) => void;
  setGraphDefinition: (graph: any) => void;
  clearSnapshots: () => void;
  clearSession: () => void;
  reset: () => void;
}

export const useRunStore = create<RunState>((set) => ({
  runId: null,
  activeFlowId: null,
  status: 'idle',
  messages: [],
  activeNodeIds: [],
  pausedNodeId: null,
  nodeLabels: {},
  currentToolName: null,
  nodeExecutionCounts: {}, 
  toolStats: {},
  tokenUsage: {},
  pendingStepTokens: {},
  nodeSnapshots: {},
  graphDefinition: null,
  iteratorProgress: {},
  logs: [],
  
  setGraphDefinition: (graph) => set({ graphDefinition: graph }),

  setRunId: (runId) => set({ runId }),
  setActiveFlowId: (activeFlowId) => set({ activeFlowId }),
  setStatus: (status) => set({ status }),
  setPaused: (pausedNodeId) => set({ status: pausedNodeId ? 'paused' : 'running', pausedNodeId }),
  
  addActiveNode: (nodeId) => set((state) => {
    if (state.activeNodeIds.includes(nodeId)) return state;
    return { activeNodeIds: [...state.activeNodeIds, nodeId] };
  }),

  removeActiveNode: (nodeId) => set((state) => ({
    activeNodeIds: state.activeNodeIds.filter(id => id !== nodeId)
  })),

  addTokenUsage: (nodeId, usage) => set((state) => {
    // 1. Accumulate Global Total
    const currentGlobal = state.tokenUsage[nodeId] || { input: 0, output: 0, total: 0 };
    const newGlobal = {
        input: currentGlobal.input + (usage.input_tokens || 0),
        output: currentGlobal.output + (usage.output_tokens || 0),
        total: currentGlobal.total + (usage.total_tokens || 0)
    };

    // 2. Accumulate Pending Step Total (since last snapshot)
    const currentPending = state.pendingStepTokens[nodeId] || { input: 0, output: 0, total: 0 };
    const newPending = {
        input: currentPending.input + (usage.input_tokens || 0),
        output: currentPending.output + (usage.output_tokens || 0),
        total: currentPending.total + (usage.total_tokens || 0)
    };

    return {
      tokenUsage: { ...state.tokenUsage, [nodeId]: newGlobal },
      pendingStepTokens: { ...state.pendingStepTokens, [nodeId]: newPending }
    };
  }),
  
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

  addSnapshot: (nodeId, snapshot) => set((state) => {
    // Consume pending tokens for this step
    const stepTokens = state.pendingStepTokens[nodeId];
    
    // Enrich snapshot with metadata
    const enrichedSnapshot = {
        ...snapshot,
        _meta: {
            tokens: stepTokens,
            timestamp: Date.now()
        }
    };

    // Clear pending tokens for this node
    const { [nodeId]: _, ...remainingPending } = state.pendingStepTokens;

    return {
        nodeSnapshots: {
            ...state.nodeSnapshots,
            [nodeId]: [...(state.nodeSnapshots[nodeId] || []), enrichedSnapshot]
        },
        pendingStepTokens: remainingPending,
        logs: [...state.logs, { level: 'info', message: `Snapshot captured for ${nodeId}`, nodeId, timestamp: Date.now(), data: enrichedSnapshot }]
    };
  }),
  
  clearSnapshots: () => set({ nodeSnapshots: {} }),

  clearSession: () => set({
    status: 'idle',
    messages: [],
    activeNodeIds: [],
    nodeExecutionCounts: {},
    toolStats: {},
    tokenUsage: {},
    pendingStepTokens: {},
    nodeSnapshots: {}, // Clear debug data too
    graphDefinition: null,
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
