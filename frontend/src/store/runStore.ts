import { create } from 'zustand';

export type MessageType = 'user' | 'ai' | 'tool' | 'trace';

export interface Message {
  id: string;
  role: MessageType;
  content: string;
  name?: string; // Logged sender name
  nodeId?: string | null; // ID of the node that generated this message
  timestamp: number;
  toolDetails?: {
    name: string;
    input: string;
    output?: string;
  };
  traceDetails?: {
    nodeId: string;
    input: string;
    count: number;
  };
}

export interface LogEntry {
  timestamp: number;
  event: string;
  details: any;
  level: 'info' | 'error' | 'warn';
}

interface RunState {
  status: 'idle' | 'connecting' | 'running' | 'error' | 'done';
  messages: Message[];
  activeNodeId: string | null;
  nodeLabels: Record<string, string>; // Map nodeId -> Label
  currentToolName: string | null;
  iteratorProgress: Record<string, { current: number; total: number }>;
  nodeExecutionCounts: Record<string, number>;
  logs: LogEntry[];
  
  // Actions
  setStatus: (status: RunState['status']) => void;
  setActiveNode: (nodeId: string | null) => void;
  setNodeLabels: (labels: Record<string, string>) => void;
  setCurrentTool: (toolName: string | null) => void;
  incrementNodeExecution: (nodeId: string) => void;
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
  activeNodeId: null,
  nodeLabels: {},
  currentToolName: null,
  nodeExecutionCounts: {}, 
  iteratorProgress: {},
  logs: [],

  setStatus: (status) => set({ status }),
  
  setActiveNode: (activeNodeId) => set({ activeNodeId }),
  
  setNodeLabels: (nodeLabels) => set({ nodeLabels }),

  setCurrentTool: (currentToolName) => set({ currentToolName }),

  incrementNodeExecution: (nodeId) => set((state) => ({
    nodeExecutionCounts: {
      ...state.nodeExecutionCounts,
      [nodeId]: (state.nodeExecutionCounts[nodeId] || 0) + 1
    }
  })),

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
    
    // Check if the last message is from AI AND matches the current active node
    // This allows separating messages from different agents even if they run sequentially
    const isSameNode = lastMsg && lastMsg.role === 'ai' && lastMsg.nodeId === state.activeNodeId;

    if (isSameNode) {
        const updatedMsg = { ...lastMsg, content: lastMsg.content + token };
        messages[messages.length - 1] = updatedMsg;
        return { messages };
    } else {
        // If last message was user, tool, or different agent, create a new AI message
        const senderName = state.activeNodeId ? state.nodeLabels[state.activeNodeId] : undefined;
        return {
            messages: [
                ...messages,
                {
                    id: crypto.randomUUID(),
                    role: 'ai',
                    content: token,
                    name: senderName,
                    nodeId: state.activeNodeId,
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
    activeNodeId: null,
    nodeExecutionCounts: {},
    logs: []
  }),

  reset: () => set({
    status: 'idle',
    messages: [],
    activeNodeId: null,
    currentToolName: null,
    iteratorProgress: {},
    nodeExecutionCounts: {},
    logs: []
  }),
}));
