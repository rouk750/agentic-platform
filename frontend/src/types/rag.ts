import type { NodeData } from './common';

export interface RAGNodeData extends NodeData {
  label?: string;
  collection_name?: string;
  action?: 'read' | 'write'; // Deprecated, kept for backward compatibility
  capabilities?: ('read' | 'write')[]; // New: array of capabilities
  global_access?: boolean; // New: if true, tools available to all agents
  chroma?: {
    mode?: 'local' | 'server';
    path?: string;
    host?: string;
    port?: number | string;
    collection_name?: string;
  };
  isStart?: boolean;
  k?: number;
  enable_dedup?: boolean;
  dedup_threshold?: number;
  subtitle?: string;
}
