import type { NodeData } from './common';

export interface IteratorNodeData extends NodeData {
    input_list_variable?: string;
    output_item_variable?: string;
    // Potentiellement d'autres champs de configuration
}
