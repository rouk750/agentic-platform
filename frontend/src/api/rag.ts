import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/rag',
});

export interface RagPreviewRequest {
  config: {
    collection_name: string;
    mode: 'local' | 'server';
    path?: string;
    host?: string;
    port?: number;
    embedding_model?: string;
  };
  limit?: number;
  offset?: number;
}

export interface RagTestRequest {
  query: string;
  k?: number;
  config: {
    collection_name: string;
    mode: 'local' | 'server';
    path?: string;
    host?: string;
    port?: number;
    embedding_model?: string;
  };
}

export interface RagDocument {
  id: string;
  excerpt: string;
  metadata: Record<string, any>;
}

export interface RagPreviewResponse {
  items: RagDocument[];
  total: number;
  error?: string;
}

export interface RagPurgeConfig {
  config: {
    collection_name: string;
    mode: 'local' | 'server';
    path?: string;
    host?: string;
    port?: number;
    embedding_model?: string;
  };
}

export const getCollectionPreview = async (
  params: RagPreviewRequest
): Promise<RagPreviewResponse> => {
  const response = await api.post('/preview', params);
  return response.data;
};

export const testSearch = async (params: RagTestRequest): Promise<{ result: string }> => {
  const response = await api.post('/test', params);
  return response.data;
};

export const purgeCollection = async (
  params: RagPurgeConfig
): Promise<{ status: string; message: string }> => {
  const response = await api.delete('/purge', { data: params });
  return response.data;
};
