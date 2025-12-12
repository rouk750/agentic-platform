import { create } from 'zustand';

export type MessageType = 'user' | 'ai' | 'tool';

export interface Message {
  id: string;
  role: MessageType;
  content: string;
  name?: string; // Logged sender name
  timestamp: number;
  toolDetails?: {
    name: string;
    input: string;
    output?: string;
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
  logs: LogEntry[];
  
  // Actions
  setStatus: (status: RunState['status']) => void;
  setActiveNode: (nodeId: string | null) => void;
  setNodeLabels: (labels: Record<string, string>) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  appendToken: (token: string) => void;
  addLog: (entry: Omit<LogEntry, 'timestamp'>) => void;
  clearSession: () => void;
}

export const useRunStore = create<RunState>((set) => ({
  status: 'idle',
  messages: [],
  activeNodeId: null,
  nodeLabels: {},
  logs: [],

  setStatus: (status) => set({ status }),
  
  setActiveNode: (activeNodeId) => set({ activeNodeId }),
  
  setNodeLabels: (nodeLabels) => set({ nodeLabels }),
  
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
    
    // Only append if the last message is from AI and MATCHES current active node if possible?
    // Simply checking role 'ai' is usually enough for streaming.
    if (lastMsg && lastMsg.role === 'ai') {
        const updatedMsg = { ...lastMsg, content: lastMsg.content + token };
        messages[messages.length - 1] = updatedMsg;
        return { messages };
    } else {
        // If last message was user or tool, create a new AI message
        const senderName = state.activeNodeId ? state.nodeLabels[state.activeNodeId] : undefined;
        return {
            messages: [
                ...messages,
                {
                    id: crypto.randomUUID(),
                    role: 'ai',
                    content: token,
                    name: senderName,
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
    logs: []
  }),
}));
