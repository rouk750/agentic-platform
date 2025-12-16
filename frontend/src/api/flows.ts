import axios from 'axios';

// Define Flow Type
export interface Flow {
    id?: number;
    name: string;
    description?: string;
    is_archived?: boolean;
    data: string; // JSON string
    created_at?: string;
    updated_at?: string;
}

const getBaseUrl = async () => {
    if ((window as any).electronAPI) {
        const port = await (window as any).electronAPI.getApiPort();
        return `http://localhost:${port}/api`;
    }
    return "http://localhost:8000/api";
};

export const flowApi = {
    getAll: async (): Promise<Flow[]> => {
        const baseUrl = await getBaseUrl();
        const res = await axios.get(`${baseUrl}/flows`);
        return res.data;
    },

    getOne: async (id: number): Promise<Flow> => {
        const baseUrl = await getBaseUrl();
        const res = await axios.get(`${baseUrl}/flows/${id}`);
        return res.data;
    },

    create: async (flow: Flow): Promise<Flow> => {
        const baseUrl = await getBaseUrl();
        const res = await axios.post(`${baseUrl}/flows`, flow);
        return res.data;
    },

    update: async (id: number, flow: Partial<Flow>): Promise<Flow> => {
        const baseUrl = await getBaseUrl();
        const res = await axios.put(`${baseUrl}/flows/${id}`, flow);
        return res.data;
    },

    delete: async (id: number): Promise<void> => {
        const baseUrl = await getBaseUrl();
        await axios.delete(`${baseUrl}/flows/${id}`);
    },

    getVersions: async (flowId: number): Promise<any[]> => {
        const baseUrl = await getBaseUrl();
        const res = await axios.get(`${baseUrl}/flows/${flowId}/versions`, {
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Expires': '0',
            }
        });
        return res.data;
    },

    restoreVersion: async (flowId: number, versionId: number): Promise<Flow> => {
        const baseUrl = await getBaseUrl();
        const res = await axios.post(`${baseUrl}/flows/${flowId}/versions/${versionId}/restore`);
        return res.data;
    },

    deleteVersion: async (flowId: number, versionId: number): Promise<void> => {
        const baseUrl = await getBaseUrl();
        await axios.delete(`${baseUrl}/flows/${flowId}/versions/${versionId}`);
    },

    deleteVersions: async (flowId: number, versionIds: number[]): Promise<void> => {
        const baseUrl = await getBaseUrl();
        await axios.delete(`${baseUrl}/flows/${flowId}/versions`, {
            data: versionIds
        });
    },

    toggleLock: async (flowId: number, versionId: number, isLocked: boolean): Promise<void> => {
        const baseUrl = await getBaseUrl();
        await axios.put(`${baseUrl}/flows/${flowId}/versions/${versionId}/lock`, null, {
            params: { is_locked: isLocked }
        });
    }
};
