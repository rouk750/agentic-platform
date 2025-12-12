
export interface LLMProfile {
    id: number;
    name: string;
    provider: 'openai' | 'anthropic' | 'mistral' | 'ollama' | 'azure' | 'lmstudio';
    model_id: string;
    base_url?: string;
    temperature: number;
}

export interface LLMProfileCreate {
    name: string;
    provider: string;
    model_id: string;
    api_key?: string;
    base_url?: string;
}
