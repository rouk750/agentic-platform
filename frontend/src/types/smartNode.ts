import type { NodeData } from './common';

export type SmartNodeMode = 'ChainOfThought' | 'Predict';

export interface IOSpec {
    name: string;
    desc?: string;
}

export interface SmartNodeData extends NodeData {
    mode?: SmartNodeMode;
    goal?: string;
    inputs?: IOSpec[];
    outputs?: IOSpec[];
    examples?: any[]; // Peut être affiné plus tard si structure connue
}
