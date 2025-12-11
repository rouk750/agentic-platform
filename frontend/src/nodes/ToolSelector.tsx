import { useEffect, useState } from 'react';
import axios from 'axios';
import { Loader2 } from 'lucide-react';

interface Tool {
    id: string;
    name: string;
    description: string;
}

interface ToolSelectorProps {
    selectedTools: string[];
    onChange: (tools: string[]) => void;
}

export function ToolSelector({ selectedTools, onChange }: ToolSelectorProps) {
    const [tools, setTools] = useState<Tool[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTools = async () => {
            try {
                // Should use settings.ts or similar helper but axios is fine for now
                // Need to get port
                let port = 8000;
                if ((window as any).electronAPI) {
                    port = await (window as any).electronAPI.getApiPort();
                }
                const res = await axios.get(`http://localhost:${port}/api/tools`);
                setTools(res.data);
            } catch (e) {
                console.error("Failed to fetch tools", e);
            } finally {
                setLoading(false);
            }
        };
        fetchTools();
    }, []);

    const toggleTool = (toolName: string) => {
        if (selectedTools.includes(toolName)) {
            onChange(selectedTools.filter(t => t !== toolName));
        } else {
            onChange([...selectedTools, toolName]);
        }
    };

    if (loading) {
        return <div className="text-xs text-slate-400 flex gap-1"><Loader2 size={12} className="animate-spin" /> Loading tools...</div>;
    }

    if (tools.length === 0) {
        return <div className="text-xs text-slate-400">No tools found.</div>;
    }

    return (
        <div className="flex flex-col gap-1 max-h-32 overflow-y-auto">
            {tools.map(tool => (
                <label key={tool.id} className="flex items-center gap-2 text-sm text-slate-700 hover:bg-slate-50 p-1 rounded cursor-pointer">
                    <input
                        type="checkbox"
                        checked={selectedTools.includes(tool.name)}
                        onChange={() => toggleTool(tool.name)}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span title={tool.description}>{tool.name}</span>
                </label>
            ))}
        </div>
    );
}
