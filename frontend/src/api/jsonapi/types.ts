/**
 * JSON:API Types
 * 
 * TypeScript interfaces for JSON:API specification.
 * Reference: https://jsonapi.org/format/
 */

// Generic JSON:API types

export interface JSONAPIResource<TAttributes = Record<string, unknown>> {
  type: string;
  id: string;
  attributes: TAttributes;
  relationships?: Record<string, JSONAPIRelationship>;
  links?: JSONAPILinks;
}

export interface JSONAPIRelationship {
  data?: JSONAPIResourceIdentifier | JSONAPIResourceIdentifier[] | null;
  links?: JSONAPILinks;
}

export interface JSONAPIResourceIdentifier {
  type: string;
  id: string;
}

export interface JSONAPILinks {
  self?: string;
  related?: string;
  first?: string;
  last?: string;
  prev?: string;
  next?: string;
}

export interface JSONAPIMeta {
  total?: number;
  page?: number;
  per_page?: number;
  total_pages?: number;
}

export interface JSONAPIDocument<TAttributes = Record<string, unknown>> {
  data: JSONAPIResource<TAttributes> | JSONAPIResource<TAttributes>[];
  meta?: JSONAPIMeta;
  links?: JSONAPILinks;
  included?: JSONAPIResource[];
}

export interface JSONAPISingleDocument<TAttributes = Record<string, unknown>> {
  data: JSONAPIResource<TAttributes>;
  meta?: JSONAPIMeta;
  links?: JSONAPILinks;
}

export interface JSONAPICollectionDocument<TAttributes = Record<string, unknown>> {
  data: JSONAPIResource<TAttributes>[];
  meta?: JSONAPIMeta;
  links?: JSONAPILinks;
}

// Error types

export interface JSONAPIError {
  status: string;
  code: string;
  title: string;
  detail?: string;
  source?: {
    pointer?: string;
    parameter?: string;
  };
  meta?: Record<string, unknown>;
}

export interface JSONAPIErrorResponse {
  errors: JSONAPIError[];
}

// Domain-specific attribute types

export interface FlowAttributes {
  name: string;
  description?: string;
  is_archived: boolean;
  data: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface FlowVersionAttributes {
  flow_id: number;
  data: string;
  is_locked: boolean;
  created_at: string | null;
}

export interface LLMProfileAttributes {
  name: string;
  provider: string;
  model_id: string;
  base_url?: string;
  temperature?: number;
  has_api_key: boolean;
}

export interface AgentTemplateAttributes {
  name: string;
  description?: string;
  type: string;
  config: string;
  is_archived: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// Type aliases for convenience
export type FlowResource = JSONAPIResource<FlowAttributes>;
export type FlowVersionResource = JSONAPIResource<FlowVersionAttributes>;
export type LLMProfileResource = JSONAPIResource<LLMProfileAttributes>;
export type AgentTemplateResource = JSONAPIResource<AgentTemplateAttributes>;

export type FlowDocument = JSONAPISingleDocument<FlowAttributes>;
export type FlowCollectionDocument = JSONAPICollectionDocument<FlowAttributes>;
export type FlowVersionCollectionDocument = JSONAPICollectionDocument<FlowVersionAttributes>;
export type LLMProfileCollectionDocument = JSONAPICollectionDocument<LLMProfileAttributes>;
