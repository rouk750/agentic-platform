
export type MessageType = 'user' | 'ai' | 'tool' | 'trace' | 'system';

export interface ToolDetails {
    name: string;
    input: string;
    output?: string;
}

export interface TraceDetails {
    nodeId: string;
    input: string;
    count: number;
}

export interface Message {
  id: string;
  role: MessageType;
  content: string;
  name?: string; // Logged sender name
  nodeId?: string | null; // ID of the node that generated this message
  timestamp: number;
  toolDetails?: ToolDetails;
  traceDetails?: TraceDetails;
}

export interface LogEntry {
  timestamp: number;
  event: string;
  details: unknown;
  level: 'info' | 'error' | 'warn';
}
