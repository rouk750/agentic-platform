import { NodeData } from './common';

export type RouteConditionType = 'equals' | 'contains' | 'regex' | 'default';

export interface RouteCondition {
    id: string;
    target_handle?: string;
    source?: 'message' | 'context';
    context_key?: string;
    condition: RouteConditionType;
    value: string;
}

export interface RouterNodeData extends NodeData {
    routes?: RouteCondition[];
}
