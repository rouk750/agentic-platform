import type { NodeData } from './common';

export type SmartNodeMode = 'ChainOfThought' | 'Predict';

export interface IOSpec {
  name: string;
  desc?: string;
}

export interface Example {
  inputs: Record<string, string>;
  outputs: Record<string, string>;
}

export interface SmartNodeData extends NodeData {
  mode?: SmartNodeMode;
  goal?: string;
  inputs?: IOSpec[];
  outputs?: IOSpec[];
  examples?: Example[];
  llm_profile?: unknown; // Can be string ID or object
  maxRounds?: number;
  optimizationResult?: unknown;
  // Template Versioning
  _templateId?: number;
  _templateVersion?: number;
}
