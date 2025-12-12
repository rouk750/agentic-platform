import axios from 'axios';

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
