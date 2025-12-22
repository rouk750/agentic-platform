/**
 * Domain Types - Agent Templates
 *
 * Centralized type definitions for AgentTemplate entities.
 */

/**
 * Agent template - reusable agent configuration.
 */
export interface AgentTemplate {
  id: number;
  name: string;
  description?: string;
  type: 'agent' | 'smart_node'; // Node type
  config: string; // JSON configuration
  is_archived: boolean;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Template creation payload.
 */
export type AgentTemplateCreate = Omit<
  AgentTemplate,
  'id' | 'created_at' | 'updated_at' | 'is_archived'
> & {
  is_archived?: boolean;
};

/**
 * Template update payload.
 */
export type AgentTemplateUpdate = Partial<Omit<AgentTemplate, 'id' | 'created_at' | 'updated_at'>>;

/**
 * Agent template version - historical snapshot.
 */
export interface AgentTemplateVersion {
  id: number;
  template_id: number;
  config: string;
  version_number: number;
  is_locked: boolean;
  created_at: string | null;
}
