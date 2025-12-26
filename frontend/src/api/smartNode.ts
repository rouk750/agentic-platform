import axios from 'axios';

const getBaseUrl = async () => {
  return 'http://localhost:8000/api';
};

export interface GuardrailDefinition {
  id: string;
  label: string;
  description: string;
  params: Array<{ name: string; type: string; label: string }>;
}

export interface GuardrailConfig {
  id: string;
  params?: Record<string, any>;
}

export interface OptimizationPayload {
  node_id: string;
  goal: string;
  mode: string;
  inputs: { name: string; desc: string }[];
  outputs: {
    name: string;
    desc: string;
    guardrail?: GuardrailConfig;
    guardrails?: GuardrailConfig[];
  }[];
  examples: any[];
  llm_profile_id: number;
  metric: string;
  max_rounds?: number;
}

export const getAvailableGuardrails = async (): Promise<GuardrailDefinition[]> => {
  const baseUrl = await getBaseUrl();
  const response = await axios.get(`${baseUrl}/guardrails`);
  return response.data;
};

export const optimizeNode = async (payload: OptimizationPayload) => {
  const baseUrl = await getBaseUrl();
  const response = await axios.post(`${baseUrl}/smart-nodes/optimize`, payload);
  return response.data;
};
