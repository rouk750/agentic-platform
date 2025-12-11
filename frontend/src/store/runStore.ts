import { create } from 'zustand';

export type MessageType = 'user' | 'ai' | 'tool';

export interface Message {
  id: string;
  role: MessageType;
  content: string;
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
  logs: LogEntry[];
  
  // Actions
  setStatus: (status: RunState['status']) => void;
  setActiveNode: (nodeId: string | null) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  appendToken: (token: string) => void;
  addLog: (entry: Omit<LogEntry, 'timestamp'>) => void;
  clearSession: () => void;
}

export const useRunStore = create<RunState>((set) => ({
  status: 'idle',
  messages: [],
  activeNodeId: null,
  logs: [],

  setStatus: (status) => set({ status }),
  
  setActiveNode: (activeNodeId) => set({ activeNodeId }),
  
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
    
    // Only append if the last message is from AI
    if (lastMsg && lastMsg.role === 'ai') {
        const updatedMsg = { ...lastMsg, content: lastMsg.content + token };
        messages[messages.length - 1] = updatedMsg;
        return { messages };
    } else {
        // If last message was user or tool, create a new AI message
        return {
            messages: [
                ...messages,
                {
                    id: crypto.randomUUID(),
                    role: 'ai',
                    content: token,
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
