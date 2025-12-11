import axios from 'axios';

const getBaseUrl = async () => {
    return "http://localhost:8000/api";
};

export interface OptimizationPayload {
    node_id: string;
    goal: string;
    mode: string;
    inputs: { name: string; desc: string }[];
    outputs: { name: string; desc: string }[];
    examples: any[];
    llm_profile_id: number;
    metric: string;
}

export const optimizeNode = async (payload: OptimizationPayload) => {
    const baseUrl = await getBaseUrl();
    const response = await axios.post(`${baseUrl}/smart-nodes/optimize`, payload);
    return response.data;
};
