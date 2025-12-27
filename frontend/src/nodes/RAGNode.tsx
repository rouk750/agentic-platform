import { Handle, Position, useReactFlow, type NodeProps, type Node } from '@xyflow/react';
import { RAGNodeConfigDialog } from './RAGNodeConfigDialog';
import { TechnicalInfoDialog } from './TechnicalInfoDialog';
import { Database, Settings2, Info, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useState } from 'react';
import { useRunStore } from '../store/runStore';

import type { RAGNodeData } from '../types/rag';

type RAGNodeType = Node<RAGNodeData>;

export function RAGNode({ id, data, selected }: NodeProps<RAGNodeType>) {
  const { updateNodeData } = useReactFlow();
  const activeNodeIds = useRunStore((state) => state.activeNodeIds);
  const isActive = activeNodeIds.includes(id);
  const [configOpen, setConfigOpen] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);

  // Support both new capabilities and old action for backward compatibility
  const capabilities =
    data.capabilities ||
    (data.action === 'read' ? ['read'] : data.action === 'write' ? ['write'] : ['read']);
  const collection = data.chroma?.collection_name || data.collection_name || 'default';
  const mode = data.chroma?.mode || 'local';

  return (
    <>
      <div
        className={twMerge(
          'bg-white border-2 rounded-xl w-72 shadow-sm transition-all duration-300 group',
          selected
            ? 'border-purple-500 ring-2 ring-purple-500/20 shadow-md'
            : 'border-slate-200 hover:border-slate-300',
          isActive && 'border-green-500 ring-4 ring-green-500/20 shadow-xl scale-105'
        )}
      >
        {/* Header */}
        <div className="flex items-center gap-3 p-3 border-b border-purple-100 bg-gradient-to-b from-purple-50/50 to-purple-100/30 rounded-t-xl">
          <div
            className={twMerge(
              'p-2 rounded-lg transition-colors bg-purple-100 text-purple-600 relative'
            )}
          >
            <Database size={18} />
            {data.isStart && (
              <div
                className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white shadow-sm flex items-center justify-center"
                title="Entry Point"
              >
                <div className="w-1 h-1 bg-white rounded-full"></div>
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <input
                className="font-bold text-slate-800 bg-transparent border-none p-0 focus:ring-0 w-full text-sm truncate placeholder:text-slate-400"
                value={String(data.label || 'RAG Node')}
                onChange={(e) => updateNodeData(id, { label: e.target.value })}
                placeholder="RAG Node"
              />
            </div>

            <div className="text-[10px] text-slate-500 font-medium flex items-center gap-1 mt-0.5">
              <span
                className={twMerge(
                  'uppercase tracking-wider px-1.5 py-0.5 rounded flex items-center gap-1',
                  capabilities.length === 2
                    ? 'bg-green-50 text-green-600'
                    : capabilities.includes('read')
                      ? 'bg-blue-50 text-blue-600'
                      : 'bg-orange-50 text-orange-600'
                )}
              >
                {capabilities.length === 2 ? (
                  <>
                    <ArrowUpCircle size={8} />
                    <ArrowDownCircle size={8} />
                    R+W
                  </>
                ) : capabilities.includes('read') ? (
                  <>
                    <ArrowDownCircle size={10} />
                    READ
                  </>
                ) : (
                  <>
                    <ArrowUpCircle size={10} />
                    WRITE
                  </>
                )}
              </span>
              <span className="truncate text-slate-400">
                | {mode} : {collection}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setInfoOpen(true)}
              className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              title="Technical Info"
            >
              <Info size={16} />
            </button>
            <button
              onClick={() => setConfigOpen(true)}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
            >
              <Settings2 size={16} />
            </button>
          </div>
        </div>

        {/* Body Summary */}
        <div className="p-3">
          <div className="flex gap-2 text-[10px] font-mono">
            {capabilities.length === 2 ? (
              // Both read and write
              <>
                <div className="flex-1 bg-slate-50 border border-slate-100 rounded px-2 py-1 text-slate-500">
                  Content
                </div>
                <div className="flex items-center text-slate-300">⇄</div>
                <div className="flex-1 bg-green-50 border border-green-100 rounded px-2 py-1 text-green-700">
                  Stored+Context
                </div>
              </>
            ) : capabilities.includes('read') ? (
              // Read only
              <>
                <div className="flex-1 bg-slate-50 border border-slate-100 rounded px-2 py-1 text-slate-500">
                  Query
                </div>
                <div className="flex items-center text-slate-300">→</div>
                <div className="flex-1 bg-purple-50 border border-purple-100 rounded px-2 py-1 text-purple-700">
                  Context
                </div>
              </>
            ) : (
              // Write only
              <>
                <div className="flex-1 bg-slate-50 border border-slate-100 rounded px-2 py-1 text-slate-500">
                  Content
                </div>
                <div className="flex items-center text-slate-300">→</div>
                <div className="flex-1 bg-purple-50 border border-purple-100 rounded px-2 py-1 text-purple-700">
                  Stored
                </div>
              </>
            )}
          </div>
        </div>

        {/* Handles */}
        <div className="absolute -left-3 top-1/2 flex items-center">
          <Handle
            type="target"
            position={Position.Left}
            className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white transition-transform hover:scale-125"
          />
        </div>
        <div className="absolute -right-3 top-1/2 flex items-center">
          <Handle
            type="source"
            position={Position.Right}
            className="!w-3 !h-3 !bg-green-500 !border-2 !border-white transition-transform hover:scale-125"
          />
        </div>
      </div>

      <RAGNodeConfigDialog
        open={configOpen}
        onOpenChange={setConfigOpen}
        data={{ ...data, id }}
        onUpdate={(updates) => updateNodeData(id, updates)}
      />

      <TechnicalInfoDialog open={infoOpen} onOpenChange={setInfoOpen} data={{ ...data, id }} />
    </>
  );
}
