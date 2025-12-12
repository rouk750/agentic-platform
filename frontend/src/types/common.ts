export interface NodeData {
    label?: string;
    [key: string]: unknown;
}

export interface SchemaField {
    name: string;
    description: string;
    type: 'string' | 'number' | 'boolean' | 'array';
}
