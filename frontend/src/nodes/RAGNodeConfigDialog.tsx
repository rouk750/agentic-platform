import * as Dialog from '@radix-ui/react-dialog';
import { X, Save, Loader2, Database, Server, HardDrive, Globe } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

import { getCollectionPreview, testSearch, purgeCollection, type RagDocument } from '../api/rag';
import { Trash2, AlertTriangle } from 'lucide-react';

import type { RAGNodeData } from '../types/rag';

interface RAGNodeConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: RAGNodeData & { id?: string };
  onUpdate: (data: RAGNodeData) => void;
}

export function RAGNodeConfigDialog({
  open,
  onOpenChange,
  data,
  onUpdate,
}: RAGNodeConfigDialogProps) {
  // Config state
  const [collectionName, setCollectionName] = useState(data.collection_name || 'default');

  // New: Capabilities (replaces action)
  const [capabilities, setCapabilities] = useState<('read' | 'write')[]>(() => {
    if (data.capabilities) {
      return data.capabilities;
    }
    // Backward compatibility: migrate from action
    if (data.action === 'read') return ['read'];
    if (data.action === 'write') return ['write'];
    return ['read']; // Default
  });

  // New: Global access
  const [globalAccess, setGlobalAccess] = useState(data.global_access || false);

  const [isStart, setIsStart] = useState(data.isStart || false);
  const [k, setK] = useState(data.k || 5);

  // Deduplication Config
  const [enableDedup, setEnableDedup] = useState(data.enable_dedup !== false);
  const [dedupThreshold, setDedupThreshold] = useState(data.dedup_threshold || 0.95);

  // Chroma Config
  const [mode, setMode] = useState<'local' | 'server'>(
    (data.chroma?.mode as 'local' | 'server') || 'local'
  );
  const [path, setPath] = useState(data.chroma?.path || './chroma_db');
  const [host, setHost] = useState(data.chroma?.host || 'localhost');
  const [port, setPort] = useState(data.chroma?.port || '8000');

  // Browser State
  const [activeTab, setActiveTab] = useState<'settings' | 'browser'>('settings');
  const [browserItems, setBrowserItems] = useState<RagDocument[]>([]);
  const [browserTotal, setBrowserTotal] = useState(0);
  const [browserLoading, setBrowserLoading] = useState(false);
  const [browserOffset, setBrowserOffset] = useState(0);
  const [testQuery, setTestQuery] = useState('');
  const [testResult, setTestResult] = useState('');

  const [testLoading, setTestLoading] = useState(false);

  // Purge State
  const [purgeDialogOpen, setPurgeDialogOpen] = useState(false);
  const [purgeLoading, setPurgeLoading] = useState(false);

  // Sync state when data changes or dialog opens
  useEffect(() => {
    if (open) {
      setCollectionName(data.chroma?.collection_name || data.collection_name || 'default');

      // Sync capabilities
      if (data.capabilities) {
        setCapabilities(data.capabilities);
      } else if (data.action) {
        // Backward compatibility
        if (data.action === 'read') setCapabilities(['read']);
        else if (data.action === 'write') setCapabilities(['write']);
      }

      setGlobalAccess(data.global_access || false);
      setMode(data.chroma?.mode || 'local');
      setPath(data.chroma?.path || './chroma_db');
      setHost(data.chroma?.host || 'localhost');
      setPort(data.chroma?.port || '8000');
      setIsStart(data.isStart || false);
      setK(data.k || 5);
      setEnableDedup(data.enable_dedup !== false);
      setDedupThreshold(data.dedup_threshold || 0.95);
    }
  }, [open, data]);

  // Fetch Documents
  const fetchDocuments = useCallback(async () => {
    setBrowserLoading(true);
    try {
      const res = await getCollectionPreview({
        config: {
          collection_name: collectionName,
          mode: mode,
          path: path,
          host: host,
          port: parseInt(String(port)) || 8000,
        },
        limit: 10,
        offset: browserOffset,
      });
      if (res.error) {
        toast.error(res.error);
      } else {
        setBrowserItems(res.items);
        setBrowserTotal(res.total);
      }
    } catch {
      toast.error('Failed to load collection');
    } finally {
      setBrowserLoading(false);
    }
  }, [browserOffset, collectionName, mode, path, host, port]);

  useEffect(() => {
    if (open && activeTab === 'browser') {
      fetchDocuments();
    }
  }, [open, activeTab, fetchDocuments]);

  const handleTestSearch = async () => {
    if (!testQuery.trim()) return;
    setTestLoading(true);
    try {
      const res = await testSearch({
        query: testQuery,
        k: k,
        config: {
          collection_name: collectionName,
          mode: mode,
          path: path,
          host: host,
          port: parseInt(String(port)) || 8000,
        },
      });
      setTestResult(res.result);
    } catch (_) {
      toast.error('Search failed');
      setTestResult('Error performing search.');
    } finally {
      setTestLoading(false);
    }
    setTestLoading(false);
  };

  const handlePurge = async () => {
    setPurgeLoading(true);
    try {
      const res = await purgeCollection({
        config: {
          collection_name: collectionName,
          mode: mode,
          path: path,
          host: host,
          port: parseInt(String(port)) || 8000,
        },
      });

      if (res.status === 'success') {
        toast.success('Collection purged successfully');
        setBrowserItems([]);
        setBrowserTotal(0);
        setPurgeDialogOpen(false);
      } else {
        toast.error(res.message || 'Failed to purge collection');
      }
    } catch (error) {
      toast.error('Error purging collection');
      console.error(error);
    } finally {
      setPurgeLoading(false);
    }
  };

  const handleSave = () => {
    onUpdate({
      ...data,
      collection: collectionName,
      collection_name: collectionName,
      capabilities,
      global_access: globalAccess,
      chroma: {
        mode,
        path: mode === 'local' ? path : undefined,
        host: mode === 'server' ? host : undefined,
        port: mode === 'server' ? parseInt(String(port)) : undefined,
        collection_name: collectionName,
      },
      isStart,
      k,
      enable_dedup: enableDedup,
      dedup_threshold: dedupThreshold,
      subtitle: `${mode.toUpperCase()} | ${collectionName}`,
    });
    onOpenChange(false);
    toast.success('RAG Configuration Saved');
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-white rounded-xl shadow-2xl z-50 p-0 border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
          {/* Header */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <Dialog.Title className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Database size={20} className="text-purple-600" />
              RAG Node Configuration
            </Dialog.Title>
            <Dialog.Close className="p-2 hover:bg-slate-100 text-slate-500 rounded-full transition-colors outline-none">
              <X size={20} />
            </Dialog.Close>
          </div>

          {/* Tabs Header */}
          <div className="flex border-b border-slate-100 bg-white sticky top-0 z-10">
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'settings'
                  ? 'border-purple-600 text-purple-700 bg-purple-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              }`}
            >
              Configuration
            </button>
            <button
              onClick={() => setActiveTab('browser')}
              className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'browser'
                  ? 'border-indigo-600 text-indigo-700 bg-indigo-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              }`}
            >
              Collection Browser
            </button>
          </div>

          <div className="p-6 space-y-6 overflow-y-auto min-h-[400px]">
            {activeTab === 'settings' ? (
              <>
                <div className="space-y-4">
                  <label className="text-sm font-semibold text-slate-700 block">General</label>
                  {/* Entry Point Toggle - Matches AgentConfigDialog style */}
                  <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-lg flex items-center justify-between">
                    <div>
                      <label
                        className="text-sm font-semibold text-slate-800 flex items-center gap-2 cursor-pointer"
                        onClick={() => setIsStart(!isStart)}
                      >
                        Set as Entry Point
                      </label>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Forces this node to be the first step in the workflow.
                      </p>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={isStart}
                        onChange={(e) => setIsStart(e.target.checked)}
                        className="w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      />
                    </div>
                  </div>
                </div>

                <div className="h-px bg-slate-100"></div>

                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-semibold text-slate-700 block mb-1">
                      Capabilities
                    </label>
                    <p className="text-xs text-slate-500 mb-3">
                      Select which operations this RAG node can perform. The LLM will decide when to
                      use each capability via tool calls.
                    </p>

                    <div className="space-y-2">
                      <label className="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                        <input
                          type="checkbox"
                          checked={capabilities.includes('read')}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setCapabilities([...capabilities, 'read']);
                            } else {
                              setCapabilities(capabilities.filter((c) => c !== 'read'));
                            }
                          }}
                          className="w-4 h-4 rounded text-purple-600 focus:ring-purple-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-sm text-slate-800">Search (Read)</div>
                          <div className="text-xs text-slate-500">
                            Allow LLM to search for context in the knowledge base
                          </div>
                        </div>
                      </label>

                      <label className="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                        <input
                          type="checkbox"
                          checked={capabilities.includes('write')}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setCapabilities([...capabilities, 'write']);
                            } else {
                              setCapabilities(capabilities.filter((c) => c !== 'write'));
                            }
                          }}
                          className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-sm text-slate-800">Ingest (Write)</div>
                          <div className="text-xs text-slate-500">
                            Allow LLM to store new information in the knowledge base
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>

                  {/* Global Access Toggle */}
                  <div className="p-3 bg-amber-50/50 border border-amber-100 rounded-lg">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={globalAccess}
                        onChange={(e) => setGlobalAccess(e.target.checked)}
                        className="w-4 h-4 rounded text-amber-600 focus:ring-amber-500"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-sm text-slate-800">
                          Make available to all agents
                        </div>
                        <div className="text-xs text-slate-500">
                          If enabled, all agents in this graph can use these RAG tools. Otherwise,
                          only explicitly connected agents can access them.
                        </div>
                      </div>
                    </label>
                  </div>
                </div>

                <div className="h-px bg-slate-100"></div>

                {/* Top K Setting (Only for Read) */}
                {capabilities.includes('read') && (
                  <div className="space-y-1 animate-in fade-in slide-in-from-top-2 duration-200">
                    <label className="text-sm font-semibold text-slate-700 flex justify-between">
                      <span>Top Result Limit (k)</span>
                      <span className="text-xs font-normal text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                        Max Context Size
                      </span>
                    </label>
                    <div className="flex items-center gap-3">
                      <input
                        type="range"
                        min="1"
                        max="20"
                        step="1"
                        value={k}
                        onChange={(e) => setK(parseInt(e.target.value))}
                        className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                      />
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={k}
                        onChange={(e) => setK(parseInt(e.target.value))}
                        className="w-16 p-2 rounded-lg border border-slate-300 text-center text-sm font-bold text-slate-700 focus:ring-2 focus:ring-purple-500 outline-none"
                      />
                    </div>
                    <p className="text-xs text-slate-400">
                      Controls how many relevant chunks are retrieved. Higher values increase
                      context but consume more tokens.
                    </p>
                  </div>
                )}

                {/* Deduplication Settings (Only for Write) */}
                {capabilities.includes('write') && (
                  <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200 bg-orange-50/50 p-3 rounded-lg border border-orange-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                          Semantic Deduplication
                        </label>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Prevents writing content if it already exists (Similarity check).
                        </p>
                      </div>
                      <input
                        type="checkbox"
                        checked={enableDedup}
                        onChange={(e) => setEnableDedup(e.target.checked)}
                        className="w-5 h-5 rounded border-slate-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
                      />
                    </div>

                    {enableDedup && (
                      <div className="pt-2 border-t border-orange-100/50">
                        <label className="text-xs font-medium text-slate-600 flex justify-between mb-1">
                          <span>Similarity Threshold</span>
                          <span className="bg-white px-1.5 rounded text-slate-500 border border-slate-100">
                            {dedupThreshold}
                          </span>
                        </label>
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] text-slate-400">Loose</span>
                          <input
                            type="range"
                            min="0.8"
                            max="0.99"
                            step="0.01"
                            value={dedupThreshold}
                            onChange={(e) => setDedupThreshold(parseFloat(e.target.value))}
                            className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-orange-500"
                          />
                          <span className="text-[10px] text-slate-400">Strict</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="h-px bg-slate-100"></div>

                <h4 className="font-medium text-sm text-slate-500 uppercase tracking-wider">
                  ChromaDB Settings
                </h4>

                <div className="space-y-3">
                  <label className="text-sm font-semibold text-slate-700 block">
                    Connection Mode
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <div
                      className={`cursor-pointer border rounded-lg p-3 flex items-center gap-3 transition-colors ${
                        mode === 'local'
                          ? 'border-indigo-500 bg-indigo-50/50 ring-1 ring-indigo-500/20'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                      onClick={() => setMode('local')}
                    >
                      <HardDrive
                        size={18}
                        className={mode === 'local' ? 'text-indigo-600' : 'text-slate-400'}
                      />
                      <div>
                        <div
                          className={`text-sm font-medium ${mode === 'local' ? 'text-indigo-900' : 'text-slate-700'}`}
                        >
                          Local
                        </div>
                        <div className="text-[10px] text-slate-500">Embedded File</div>
                      </div>
                    </div>

                    <div
                      className={`cursor-pointer border rounded-lg p-3 flex items-center gap-3 transition-colors ${
                        mode === 'server'
                          ? 'border-indigo-500 bg-indigo-50/50 ring-1 ring-indigo-500/20'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                      onClick={() => setMode('server')}
                    >
                      <Server
                        size={18}
                        className={mode === 'server' ? 'text-indigo-600' : 'text-slate-400'}
                      />
                      <div>
                        <div
                          className={`text-sm font-medium ${mode === 'server' ? 'text-indigo-900' : 'text-slate-700'}`}
                        >
                          Server
                        </div>
                        <div className="text-[10px] text-slate-500">HTTP API</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-semibold text-slate-700">Collection Name</label>
                  <input
                    value={collectionName}
                    onChange={(e) => setCollectionName(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all"
                  />
                </div>

                {mode === 'local' ? (
                  <div className="space-y-1">
                    <label className="text-sm font-semibold text-slate-700">Database Path</label>
                    <input
                      value={path}
                      onChange={(e) => setPath(e.target.value)}
                      placeholder="./chroma_db"
                      className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all font-mono"
                    />
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-sm font-semibold text-slate-700">Host</label>
                      <div className="relative">
                        <Globe size={14} className="absolute left-3 top-3 text-slate-400" />
                        <input
                          value={host}
                          onChange={(e) => setHost(e.target.value)}
                          placeholder="localhost"
                          className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className="text-sm font-semibold text-slate-700">Port</label>
                      <input
                        value={port}
                        onChange={(e) => setPort(e.target.value)}
                        placeholder="8000"
                        type="number"
                        className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all font-mono"
                      />
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                {/* Collection Header & Purge */}
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <h4 className="font-semibold text-slate-700 text-sm">
                    Collection: <span className="font-mono text-indigo-600">{collectionName}</span>
                  </h4>
                  <button
                    onClick={() => setPurgeDialogOpen(true)}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50 p-2 rounded-lg transition-colors flex items-center gap-1.5 text-xs font-medium"
                    title="Delete all documents in this collection"
                  >
                    <Trash2 size={14} />
                    Purge Collection
                  </button>
                </div>

                {/* Confirmation Dialog as Overlay */}
                {purgeDialogOpen && (
                  <div className="absolute inset-0 bg-white/95 z-20 flex items-center justify-center p-6 backdrop-blur-sm animate-in fade-in duration-200 rounded-lg">
                    <div className="bg-white border border-red-100 shadow-xl rounded-xl p-6 max-w-sm w-full space-y-4 text-center ring-1 ring-red-50">
                      <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto text-red-500">
                        <AlertTriangle size={24} />
                      </div>
                      <div className="space-y-1">
                        <h3 className="font-bold text-slate-800 text-lg">Purge Collection?</h3>
                        <p className="text-sm text-slate-500">
                          Are you sure you want to delete all documents in{' '}
                          <span className="font-mono font-medium text-slate-700">
                            {collectionName}
                          </span>
                          ?
                          <br />
                          <span className="font-semibold text-red-500">
                            This action cannot be undone.
                          </span>
                        </p>
                      </div>
                      <div className="flex gap-3 pt-2">
                        <button
                          onClick={() => setPurgeDialogOpen(false)}
                          className="flex-1 px-4 py-2 border border-slate-200 rounded-lg text-slate-600 font-medium text-sm hover:bg-slate-50 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handlePurge}
                          disabled={purgeLoading}
                          className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium text-sm hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          {purgeLoading && <Loader2 size={14} className="animate-spin" />}
                          Confirm
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Test Search Area */}
                <div className="bg-slate-50 rounded-lg p-4 border border-slate-100 space-y-3">
                  <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    Test Retrieval
                    <span className="text-[10px] bg-slate-200 text-slate-600 px-1.5 rounded">
                      k={k}
                    </span>
                  </label>
                  <div className="flex gap-2">
                    <input
                      value={testQuery}
                      onChange={(e) => setTestQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleTestSearch()}
                      placeholder="Enter a query to test semantic search..."
                      className="flex-1 p-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                    <button
                      onClick={handleTestSearch}
                      disabled={testLoading}
                      className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                    >
                      {testLoading ? <Loader2 className="animate-spin" size={16} /> : 'Search'}
                    </button>
                  </div>
                  {testResult && (
                    <div className="bg-white p-3 rounded border border-slate-200 text-xs font-mono text-slate-600 whitespace-pre-wrap max-h-40 overflow-y-auto">
                      {testResult}
                    </div>
                  )}
                </div>

                {/* Documents Table */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-slate-700 text-sm">Indexed Documents</h4>
                    <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-full">
                      Total: {browserTotal}
                    </span>
                  </div>

                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-50 border-b border-slate-200">
                        <tr>
                          <th className="px-4 py-2 font-medium text-slate-600 w-24">ID</th>
                          <th className="px-4 py-2 font-medium text-slate-600">Content Preview</th>
                          <th className="px-4 py-2 font-medium text-slate-600 w-32">Metadata</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {browserLoading ? (
                          <tr>
                            <td colSpan={3} className="px-4 py-8 text-center text-slate-400">
                              <Loader2 className="animate-spin mx-auto mb-2" size={24} />
                              Loading documents...
                            </td>
                          </tr>
                        ) : browserItems.length === 0 ? (
                          <tr>
                            <td colSpan={3} className="px-4 py-8 text-center text-slate-400">
                              No documents found in collection &quot;{collectionName}&quot;.
                            </td>
                          </tr>
                        ) : (
                          browserItems.map((item) => (
                            <tr key={item.id} className="hover:bg-slate-50/50">
                              <td
                                className="px-4 py-2 text-xs font-mono text-slate-500 truncate max-w-[100px]"
                                title={item.id}
                              >
                                {item.id.replace('id_', '')}
                              </td>
                              <td className="px-4 py-2 text-slate-700">
                                <div className="line-clamp-2 text-xs">{item.excerpt}</div>
                              </td>
                              <td className="px-4 py-2 text-xs text-slate-500">
                                <div className="flex flex-wrap gap-1">
                                  {Object.entries(item.metadata).map(([k, v]) => (
                                    <span
                                      key={k}
                                      className="bg-slate-100 px-1 rounded border border-slate-200"
                                      title={`${k}: ${v}`}
                                    >
                                      {k}
                                    </span>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>
                      Showing {browserOffset + 1}-{Math.min(browserOffset + 10, browserTotal)} of{' '}
                      {browserTotal}
                    </span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setBrowserOffset(Math.max(0, browserOffset - 10))}
                        disabled={browserOffset === 0}
                        className="px-2 py-1 border rounded hover:bg-slate-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setBrowserOffset(browserOffset + 10)}
                        disabled={browserOffset + 10 >= browserTotal}
                        className="px-2 py-1 border rounded hover:bg-slate-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex justify-end gap-3">
            <Dialog.Close asChild>
              <button className="px-4 py-2 text-slate-600 font-medium text-sm hover:bg-slate-100 rounded-lg transition-colors">
                Cancel
              </button>
            </Dialog.Close>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white font-medium text-sm rounded-lg hover:bg-indigo-700 transition-colors shadow-sm"
            >
              <Save size={16} />
              Save Configuration
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
