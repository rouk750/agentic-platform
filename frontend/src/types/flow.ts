/**
 * Domain Types - Flows
 *
 * Centralized type definitions for Flow entities.
 * These types are used throughout the frontend for both
 * legacy API responses and JSON:API deserialized objects.
 */

/**
 * Flow entity - represents a workflow graph.
 */
export interface Flow {
  id: number;
  name: string;
  description?: string;
  is_archived: boolean;
  data: string; // JSON string of the flow graph
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Flow creation payload (id not required).
 */
export type FlowCreate = Omit<Flow, 'id' | 'created_at' | 'updated_at' | 'is_archived'> & {
  is_archived?: boolean;
};

/**
 * Flow update payload (partial).
 */
export type FlowUpdate = Partial<Omit<Flow, 'id' | 'created_at' | 'updated_at'>>;

/**
 * Flow version - represents a historical snapshot of a flow.
 */
export interface FlowVersion {
  id: number;
  flow_id: number;
  data: string; // JSON string
  version_number: number;
  is_locked: boolean;
  created_at: string | null;
}
