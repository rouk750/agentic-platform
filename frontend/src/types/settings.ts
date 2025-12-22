/**
 * Domain Types - LLM Profiles
 *
 * Centralized type definitions for LLM profile entities.
 */

/**
 * Supported LLM providers.
 */
export type LLMProvider = 'openai' | 'anthropic' | 'mistral' | 'ollama' | 'azure' | 'lmstudio';

/**
 * LLM profile - model configuration.
 */
export interface LLMProfile {
  id: number;
  name: string;
  provider: LLMProvider;
  model_id: string;
  base_url?: string;
  temperature: number;
  has_api_key?: boolean;
}

/**
 * LLM profile creation payload.
 */
export interface LLMProfileCreate {
  name: string;
  provider: LLMProvider;
  model_id: string;
  api_key?: string;
  base_url?: string;
  temperature?: number;
}

/**
 * LLM profile update payload.
 */
export type LLMProfileUpdate = Partial<LLMProfileCreate>;
