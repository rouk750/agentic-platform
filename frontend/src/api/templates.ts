import axios from 'axios';
import type { AgentTemplate, AgentTemplateVersion } from '../types/template';

// Re-export for backward compatibility
export type { AgentTemplate, AgentTemplateVersion } from '../types/template';

const API_URL = 'http://localhost:8000/api';

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
        const response = await axios.get(`${API_URL}/agent-templates/${id}/versions`, {
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Expires': '0',
            }
        });
        return response.data;
    },

    restoreVersion: async (templateId: number, versionId: number): Promise<AgentTemplate> => {
        const response = await axios.post(`${API_URL}/agent-templates/${templateId}/versions/${versionId}/restore`);
        return response.data;
    },

    deleteVersion: async (templateId: number, versionId: number): Promise<void> => {
        await axios.delete(`${API_URL}/agent-templates/${templateId}/versions/${versionId}`);
    },

    deleteVersions: async (templateId: number, versionIds: number[]): Promise<void> => {
        await axios.delete(`${API_URL}/agent-templates/${templateId}/versions`, { data: versionIds });
    },

    toggleLock: async (templateId: number, versionId: number, isLocked: boolean): Promise<void> => {
        await axios.put(`${API_URL}/agent-templates/${templateId}/versions/${versionId}/lock`, null, {
            params: { is_locked: isLocked }
        });
    }
};
