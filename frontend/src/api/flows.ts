import axios from 'axios';

// Get API base URL
let API_BASE = "http://localhost:8000/api";
if ((window as any).electronAPI) {
    (window as any).electronAPI.getApiPort().then((port: number) => {
        API_BASE = `http://localhost:${port}/api`;
    });
}
// Note: This logic for base URL is a bit fragile if called immediately on load. 
// A better pattern is to use a configured axios instance or fetch the port once.
// For now, let's assume default or quick resolution.

// Define Flow Type
export interface Flow {
    id?: number;
    name: string;
    description?: string;
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

    update: async (id: number, flow: Flow): Promise<Flow> => {
        const baseUrl = await getBaseUrl();
        const res = await axios.put(`${baseUrl}/flows/${id}`, flow);
        return res.data;
    },

    delete: async (id: number): Promise<void> => {
        const baseUrl = await getBaseUrl();
        await axios.delete(`${baseUrl}/flows/${id}`);
    }
};
