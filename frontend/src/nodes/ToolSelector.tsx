import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { Loader2, ChevronRight, ChevronDown, Server, Box } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

interface Tool {
  id: string;
  name: string;
  description: string;
  server?: string;
  source?: string;
}

interface ToolSelectorProps {
  selectedTools: string[];
  onChange: (tools: string[]) => void;
}

export function ToolSelector({ selectedTools, onChange }: ToolSelectorProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);

  // Track open state for each group
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchTools = async () => {
      try {
        let port = 8000;
        // @ts-expect-error - electronAPI injected by preload script
        if (window.electronAPI) {
          // @ts-expect-error - electronAPI injected by preload script
          port = await window.electronAPI.getApiPort();
        }
        const res = await axios.get(`http://localhost:${port}/api/tools`);
        setTools(res.data);

        // Auto-open groups that have selected tools
        const initialOpen: Record<string, boolean> = {};
        res.data.forEach((t: Tool) => {
          if (selectedTools.includes(t.name)) {
            const group = t.server || 'Standard Tools';
            initialOpen[group] = true;
          }
        });
        setOpenGroups(prev => ({ ...prev, ...initialOpen }));

      } catch (e) {
        console.error('Failed to fetch tools', e);
      } finally {
        setLoading(false);
      }
    };
    fetchTools();
  }, []); // Only on mount

  // Group tools by Server
  const groupedTools = useMemo(() => {
    const groups: Record<string, Tool[]> = {};
    tools.forEach(tool => {
      const key = tool.server || 'Standard Tools';
      if (!groups[key]) groups[key] = [];
      groups[key].push(tool);
    });
    return groups;
  }, [tools]);

  // Sort groups: Standard first, then alphabetically
  const sortedGroupKeys = useMemo(() => {
    return Object.keys(groupedTools).sort((a, b) => {
      if (a === 'Standard Tools') return -1;
      if (b === 'Standard Tools') return 1;
      return a.localeCompare(b);
    });
  }, [groupedTools]);

  const toggleTool = (toolName: string) => {
    if (selectedTools.includes(toolName)) {
      onChange(selectedTools.filter((t) => t !== toolName));
    } else {
      onChange([...selectedTools, toolName]);
    }
  };

  const toggleGroup = (groupName: string, select: boolean) => {
    const groupTools = groupedTools[groupName].map(t => t.name);
    let newSelection = [...selectedTools];

    if (select) {
      // Add all from group if not present
      groupTools.forEach(t => {
        if (!newSelection.includes(t)) newSelection.push(t);
      });
    } else {
      // Remove all from group
      newSelection = newSelection.filter(t => !groupTools.includes(t));
    }
    onChange(newSelection);
  };

  if (loading) {
    return (
      <div className="text-xs text-slate-400 flex gap-1">
        <Loader2 size={12} className="animate-spin" /> Loading tools...
      </div>
    );
  }

  if (tools.length === 0) {
    return <div className="text-xs text-slate-400">No tools found.</div>;
  }

  return (
    <div className="flex flex-col gap-1 max-h-60 overflow-y-auto pr-1">
      {sortedGroupKeys.map(group => {
        const groupTools = groupedTools[group];
        const allSelected = groupTools.every(t => selectedTools.includes(t.name));
        const someSelected = groupTools.some(t => selectedTools.includes(t.name));
        const isOpen = openGroups[group] || false;
        const isStandard = group === 'Standard Tools';

        return (
          <div key={group} className="border border-slate-200 rounded-lg overflow-hidden bg-white mb-1 shrink-0">
            {/* Header */}
            <div className="flex items-center justify-between p-2 bg-slate-50 hover:bg-slate-100 transition-colors">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <button
                  type="button"
                  onClick={() => setOpenGroups(prev => ({ ...prev, [group]: !prev[group] }))}
                  className="p-0.5 hover:bg-slate-200 rounded text-slate-500"
                >
                  {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>

                <div className="flex items-center gap-1.5 truncate">
                  {isStandard ? <Box size={14} className="text-blue-500" /> : <Server size={14} className="text-purple-500" />}
                  <span className="text-sm font-semibold text-slate-700 truncate" title={group}>{group}</span>
                  <span className="text-[10px] text-slate-400">({groupTools.length})</span>
                </div>
              </div>

              {/* Select All Checkbox */}
              <input
                type="checkbox"
                className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer ml-2"
                checked={allSelected}
                ref={input => {
                  if (input) input.indeterminate = someSelected && !allSelected;
                }}
                onChange={(e) => toggleGroup(group, e.target.checked)}
                title={`Select all ${group}`}
              />
            </div>

            {/* Content */}
            {isOpen && (
              <div className="p-1 space-y-0.5 border-t border-slate-100">
                {groupTools.map(tool => (
                  <label
                    key={tool.id}
                    className="flex items-start gap-2 text-xs text-slate-600 hover:bg-slate-50 p-1.5 rounded cursor-pointer ml-6"
                  >
                    <input
                      type="checkbox"
                      checked={selectedTools.includes(tool.name)}
                      onChange={() => toggleTool(tool.name)}
                      className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <div className="font-medium text-slate-700">{tool.name}</div>
                      <div className="text-[10px] text-slate-400 line-clamp-1" title={tool.description}>
                        {tool.description}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>
        );
      })}

      {/* Custom Tool Input */}
      <div className="pt-2 mt-2 border-t border-slate-100">
        <div className="flex gap-2 mb-2">
          <input
            className="flex-1 text-xs p-1.5 rounded border border-slate-200 focus:border-blue-500 outline-none"
            placeholder="Add Custom Tool (e.g. Node Name)"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                const val = e.currentTarget.value.trim();
                if (val && !selectedTools.includes(val)) {
                  onChange([...selectedTools, val]);
                  e.currentTarget.value = '';
                }
              }
            }}
          />
        </div>

        {/* Render Selected Custom Tools that are NOT in the API list */}
        {selectedTools
          .filter((t) => !tools.find((at) => at.name === t))
          .map((t) => (
            <div
              key={t}
              className="flex items-center justify-between gap-2 text-xs text-purple-700 bg-purple-50 p-1.5 rounded mt-1 border border-purple-100"
            >
              <span>{t}</span>
              <button
                onClick={() => onChange(selectedTools.filter((st) => st !== t))}
                type="button"
                className="text-purple-400 hover:text-purple-600 font-bold px-1"
              >
                ×
              </button>
            </div>
          ))}
      </div>
    </div>
  );
}
