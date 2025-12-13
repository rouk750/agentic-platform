import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface AgentTemplate {
    id?: number;
    name: string;
    description?: string;
    type: string; // 'agent' | 'smart_node'
    config: string; // JSON
    is_archived?: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface AgentTemplateVersion {
    id: number;
    template_id: number;
    config: string;
    created_at: string;
    version_number: number;
}

export const templateApi = {
    getAll: async (): Promise<AgentTemplate[]> => {
        const response = await axios.get(`${API_URL}/agent-templates`);
        return response.data;
    },

    getOne: async (id: number): Promise<AgentTemplate> => {
        const response = await axios.get(`${API_URL}/agent-templates/${id}`);
        return response.data;
    },

    create: async (template: AgentTemplate): Promise<AgentTemplate> => {
        const response = await axios.post(`${API_URL}/agent-templates`, template);
        return response.data;
    },

    update: async (id: number, template: Partial<AgentTemplate>): Promise<AgentTemplate> => {
        const response = await axios.put(`${API_URL}/agent-templates/${id}`, template);
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await axios.delete(`${API_URL}/agent-templates/${id}`);
    },

    getVersions: async (id: number): Promise<AgentTemplateVersion[]> => {
        const response = await axios.get(`${API_URL}/agent-templates/${id}/versions`);
        return response.data;
    },

    restoreVersion: async (templateId: number, versionId: number): Promise<AgentTemplate> => {
        const response = await axios.post(`${API_URL}/agent-templates/${templateId}/versions/${versionId}/restore`);
        return response.data;
    },

    deleteVersion: async (templateId: number, versionId: number): Promise<void> => {
        await axios.delete(`${API_URL}/agent-templates/${templateId}/versions/${versionId}`);
    }
};
