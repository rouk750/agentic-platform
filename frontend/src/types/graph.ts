import type { Node, Edge } from '@xyflow/react';

// Structure attendue par le backend pour l'exécution
export interface GraphRequest {
    nodes: Node[];
    edges: Edge[];
}
