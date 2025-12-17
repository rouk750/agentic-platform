import type { SchemaField, NodeData } from './common';
export type { SchemaField };

export interface AgentNodeData extends NodeData {
    modelId?: string;
    modelName?: string;
    system_prompt?: string;
    max_iterations?: number;
    tools?: string[];
    output_schema?: SchemaField[];
    flexible_mode?: boolean;
    isStart?: boolean;
    require_approval?: boolean;
    // Backend specific fields often synced or used for mapping
    profile_id?: number;
    provider?: string;
    model_id?: string;
    // Template Versioning
    _templateId?: number;
    _templateVersion?: number;
}
