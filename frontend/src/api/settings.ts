import axios from 'axios';
import type { LLMProfile, LLMProfileCreate, LLMProfileUpdate } from '../types/settings';

const getBaseUrl = async () => {
    return "http://localhost:8000/api";
};

export const getModels = async (): Promise<LLMProfile[]> => {
    const baseUrl = await getBaseUrl();
    const response = await axios.get(`${baseUrl}/settings/models`);
    return response.data;
};

export const createModel = async (profile: LLMProfileCreate): Promise<LLMProfile> => {
    const baseUrl = await getBaseUrl();
    const response = await axios.post(`${baseUrl}/settings/models`, profile);
    return response.data;
};

export const deleteModel = async (modelId: number): Promise<void> => {
    const baseUrl = await getBaseUrl();
    await axios.delete(`${baseUrl}/settings/models/${modelId}`);
};

export const updateModel = async (modelId: number, profile: LLMProfileUpdate): Promise<LLMProfile> => {
    const baseUrl = await getBaseUrl();
    const response = await axios.put(`${baseUrl}/settings/models/${modelId}`, profile);
    return response.data;
};

export const testSavedModel = async (modelId: number): Promise<boolean> => {
    try {
        const baseUrl = await getBaseUrl();
        await axios.post(`${baseUrl}/settings/models/${modelId}/test`);
        return true;
    } catch {
        return false;
    }
};

export const scanOllamaModels = async (): Promise<string[]> => {
    try {
        const baseUrl = await getBaseUrl();
        const response = await axios.get(`${baseUrl}/settings/providers/ollama/scan`);
        return response.data.models || [];
    } catch {
        return [];
    }
};

export const scanLMStudioModels = async (): Promise<string[]> => {
    try {
        const baseUrl = await getBaseUrl();
        const response = await axios.get(`${baseUrl}/settings/providers/lmstudio/scan`);
        return response.data.models || [];
    } catch {
        return [];
    }
};

export const testConnection = async (
    provider: string, 
    modelId: string, 
    apiKey?: string, 
    baseUrl?: string
): Promise<boolean> => {
    try {
        const apiUrl = await getBaseUrl();
        await axios.post(`${apiUrl}/settings/test-connection`, {
            provider,
            model_id: modelId,
            api_key: apiKey,
            base_url: baseUrl
        });
        return true;
    } catch {
        return false;
    }
};
