import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { flowApi, type Flow } from '../api/flows';
import {
  Trash2,
  History,
  RotateCcw,
  ArrowRight,
  Loader2,
  Plus,
  Archive,
  ArchiveRestore,
  Filter,
  Lock,
  Unlock,
} from 'lucide-react';
// import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { useApiResource } from '../hooks/useApiResource';
import { useVersionHistory } from '../hooks/useVersionHistory';
import { useSortAndFilter, type SortOption } from '../hooks/useSortAndFilter';

interface FlowVersion {
  id: number;
  flow_id: number;
  created_at: string;
  data: string;
  is_locked?: boolean;
}

// type FilterStatus = 'active' | 'archived' | 'all';

export default function FlowsPage() {
  const navigate = useNavigate();
  const {
    items: flows,
    setItems: setFlows,
    loading,
    fetchAll: loadFlows,
    remove: removeFlow,
    update: updateFlow,
  } = useApiResource<Flow>({
    api: flowApi,
    messages: {
      deleteSuccess: 'Flow deleted',
      loadError: 'Failed to load flows',
      updateSuccess: 'Flow updated',
    },
    onAfterDelete: (id) => {
      if (selectedFlowId === id) {
        resetVersions();
      }
    },
    // No explicit create here as new flow usually means navigation to new editor
  });

  useEffect(() => {
    loadFlows();
  }, [loadFlows]);

  // Custom Hooks - Version History
  const {
    selectedId: selectedFlowId,
    versions,
    loading: loadingVersions,
    handleViewVersions,
    handleRestoreVersion,
    handleDeleteVersion: onDeleteVersion,
    reset: resetVersions,
    selectedVersionIds,
    toggleVersionSelection,
    handleBulkDelete,
    handleToggleLock,
    selectAllVersions,
    clearSelection,
  } = useVersionHistory<FlowVersion, Flow>({
    fetchVersions: flowApi.getVersions,
    restoreVersion: flowApi.restoreVersion,
    deleteVersion: flowApi.deleteVersion,
    deleteVersions: flowApi.deleteVersions,
    toggleLock: flowApi.toggleLock,
    onRestoreSuccess: (restored) => {
      setFlows((prev) => prev.map((f) => (f.id === restored.id ? restored : f)));
      // navigate(`/editor/${restored.id}`); // Stay on current page
    },
  });

  // Custom Hooks - Sort and Filter
  const {
    filterStatus,
    setFilterStatus,
    sortBy,
    setSortBy,
    filteredAndSortedItems: filteredFlows,
  } = useSortAndFilter<Flow>({
    items: flows,
    filterPredicate: (item, status) => {
      if (status === 'all') return true;
      if (status === 'active') return !item.is_archived;
      if (status === 'archived') return !!item.is_archived;
      return true;
    },
    sortComparator: (a, b, sortOption) => {
      if (sortOption === 'name_asc') return a.name.localeCompare(b.name);
      const dateA = new Date(a.updated_at || 0).getTime();
      const dateB = new Date(b.updated_at || 0).getTime();
      return sortOption === 'updated_desc' ? dateB - dateA : dateA - dateB;
    },
  });

  // Wrapped handlers
  const handleViewVersionsClick = (id: number) => handleViewVersions(id);
  const handleDeleteVersionClick = (flowId: number, versionId: number) =>
    onDeleteVersion(flowId, versionId);

  const handleDeleteFlow = async (id: number) => {
    const flow = flows.find((f) => f.id === id);
    if (
      !confirm(
        `Are you sure you want to delete the flow "${flow?.name || 'Unknown'}"?\n\nThis action cannot be undone and will delete all associated versions.`
      )
    )
      return;
    await removeFlow(id);
  };

  const handleToggleArchive = async (flow: Flow) => {
    if (!flow.id) return;
    await updateFlow(flow.id, { ...flow, is_archived: !flow.is_archived });
  };

  // Filter and Sort Logic - Now handled by useSortAndFilter hook
  // const filteredFlows = flows
  //     .filter(flow => {
  //         if (filterStatus === 'all') return true;
  //         if (filterStatus === 'active') return !flow.is_archived;
  //         if (filterStatus === 'archived') return flow.is_archived;
  //         return true;
  //     })
  //     .sort((a, b) => {
  //         if (sortBy === 'name_asc') return a.name.localeCompare(b.name);
  //         const dateA = new Date(a.updated_at || 0).getTime();
  //         const dateB = new Date(b.updated_at || 0).getTime();
  //         return sortBy === 'updated_desc' ? dateB - dateA : dateA - dateB;
  //     });

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header and Toolbar */}
        <div className="flex flex-col gap-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-slate-800">Flows Management</h1>
              <p className="text-slate-500">Manage your flows and their history</p>
            </div>
            <button
              onClick={() => navigate('/editor/new')}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm font-medium"
            >
              <Plus size={18} /> New Flow
            </button>
          </div>

          <div className="flex items-center justify-between bg-white p-2 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
              <button
                onClick={() => setFilterStatus('active')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${filterStatus === 'active' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              >
                Active
              </button>
              <button
                onClick={() => setFilterStatus('archived')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${filterStatus === 'archived' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              >
                Archived
              </button>
              <button
                onClick={() => setFilterStatus('all')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${filterStatus === 'all' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              >
                All
              </button>
            </div>

            <div className="flex items-center gap-2 px-2">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Sort by
                </span>
              </div>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 outline-none"
              >
                <option value="updated_desc">Last Updated (Newest)</option>
                <option value="updated_asc">Last Updated (Oldest)</option>
                <option value="name_asc">Name (A-Z)</option>
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="animate-spin text-blue-600" size={32} />
          </div>
        ) : filteredFlows.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-slate-200 shadow-sm">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 mb-4">
              <Filter className="text-slate-400" size={24} />
            </div>
            <h3 className="text-lg font-medium text-slate-900 mb-1">No flows found</h3>
            <p className="text-slate-500 mb-4">
              {filterStatus === 'active'
                ? "You don't have any active flows."
                : filterStatus === 'archived'
                  ? "You don't have any archived flows."
                  : 'No flows match your criteria.'}
            </p>
            {filterStatus === 'active' && (
              <button
                onClick={() => navigate('/editor/new')}
                className="text-blue-600 hover:underline font-medium"
              >
                Create a new flow
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredFlows.map((flow) => (
              <div
                key={flow.id}
                className={`bg-white rounded-xl border-l-[4px] border border-slate-200 shadow-sm overflow-hidden transition-all hover:shadow-md ${flow.is_archived ? 'border-l-slate-400 bg-slate-50/50' : 'border-l-blue-500'}`}
              >
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center ${flow.is_archived ? 'bg-slate-100 text-slate-500' : 'bg-blue-50 text-blue-600'}`}
                    >
                      {flow.is_archived ? (
                        <Archive size={20} />
                      ) : (
                        <ArrowRight size={20} className="rotate-[-45deg]" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3
                          className={`font-semibold ${flow.is_archived ? 'text-slate-500 decoration-slate-400' : 'text-slate-800'}`}
                        >
                          {flow.name}
                        </h3>
                        {flow.is_archived && (
                          <span className="text-[10px] font-bold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded uppercase tracking-wider">
                            Archived
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-500 flex gap-3">
                        <span>ID: {flow.id}</span>
                        <span>•</span>
                        <span>
                          Updated{' '}
                          {formatDistanceToNow(new Date(flow.updated_at || new Date()), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggleArchive(flow)}
                      className="p-2 hover:bg-slate-100 text-slate-500 rounded-lg transition-colors"
                      title={flow.is_archived ? 'Unarchive Flow' : 'Archive Flow'}
                    >
                      {flow.is_archived ? <ArchiveRestore size={16} /> : <Archive size={16} />}
                    </button>
                    <button
                      onClick={() => flow.id && handleViewVersionsClick(flow.id)}
                      className={`p-2 rounded-lg transition-colors flex items-center gap-1.5 text-sm font-medium ${selectedFlowId === flow.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-50 text-slate-600'}`}
                    >
                      <History size={16} />
                      {selectedFlowId === flow.id ? 'Hide History' : 'History'}
                    </button>
                    <button
                      onClick={() => navigate(`/editor/${flow.id}`)}
                      className="p-2 hover:bg-slate-50 text-slate-600 rounded-lg transition-colors"
                      title="Edit Flow"
                    >
                      <span className="flex items-center gap-1.5 text-sm font-medium">Edit</span>
                    </button>
                    <button
                      onClick={() => flow.id && handleDeleteFlow(flow.id)}
                      className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors"
                      title="Delete Flow"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                {/* Versions List - Expandable */}
                {selectedFlowId === flow.id && (
                  <div className="bg-slate-50 border-t border-slate-200 p-4 animate-in slide-in-from-top-2 duration-200">
                    <div className="flex items-center justify-between mb-3 pl-1">
                      <div className="flex items-center gap-3">
                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          Version History
                        </h4>
                        {versions.length > 0 && (
                          <div className="flex items-center gap-2">
                            <div className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={
                                  selectedVersionIds.size > 0 &&
                                  versions
                                    .filter((v) => !v.is_locked && v.data !== flow.data)
                                    .every((v) => selectedVersionIds.has(v.id))
                                }
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    selectAllVersions((v) => !v.is_locked && v.data !== flow.data);
                                  } else {
                                    clearSelection();
                                  }
                                }}
                                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                              />
                              <span className="text-xs text-slate-400">Select All</span>
                            </div>

                            {selectedVersionIds.size > 0 && (
                              <div className="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 duration-200 ml-2">
                                <span className="text-xs font-medium text-slate-600">
                                  ({selectedVersionIds.size})
                                </span>
                                <button
                                  onClick={() => flow.id && handleBulkDelete(flow.id)}
                                  className="flex items-center gap-1.5 px-2 py-1 bg-red-50 text-red-600 hover:bg-red-100 rounded-md text-xs font-medium transition-colors"
                                >
                                  <Trash2 size={12} /> Delete
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {loadingVersions ? (
                      <div className="flex items-center gap-2 text-slate-500 text-sm pl-1">
                        <Loader2 className="animate-spin" size={14} /> Loading versions...
                      </div>
                    ) : versions.length === 0 ? (
                      <p className="text-sm text-slate-500 pl-1">
                        No history available for this flow.
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {versions.map((version) => {
                          const isActive = flow.data === version.data;
                          const isSelected = selectedVersionIds.has(version.id);
                          return (
                            <div
                              key={version.id}
                              className={`flex items-center justify-between bg-white p-3 rounded-lg border text-sm transition-colors ${isSelected ? 'border-blue-300 bg-blue-50/20' : isActive ? 'border-green-200 bg-green-50/30' : 'border-slate-200 hover:border-slate-300'}`}
                            >
                              <div className="flex items-center gap-3">
                                <div className="flex items-center justify-center w-6 h-6">
                                  {!version.is_locked && !isActive && (
                                    <input
                                      type="checkbox"
                                      checked={isSelected}
                                      onChange={() => toggleVersionSelection(version.id)}
                                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
                                    />
                                  )}
                                </div>
                                <span
                                  className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${isActive ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}
                                >
                                  v{version.id}
                                </span>
                                <div className="flex flex-col">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-slate-700">
                                      Saved Version
                                    </span>
                                    {isActive && (
                                      <span className="text-[10px] font-bold text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full uppercase tracking-wider">
                                        Active
                                      </span>
                                    )}
                                    {version.is_locked && (
                                      <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded-full uppercase tracking-wider flex items-center gap-1">
                                        <Lock size={8} /> Locked
                                      </span>
                                    )}
                                  </div>
                                  <span className="text-xs text-slate-500">
                                    {new Date(version.created_at).toLocaleString()} (
                                    {formatDistanceToNow(new Date(version.created_at))} ago)
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                {!isActive && (
                                  <button
                                    onClick={() =>
                                      flow.id && handleRestoreVersion(flow.id, version.id)
                                    }
                                    className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-blue-50 text-blue-600 rounded-md transition-colors text-xs font-medium border border-transparent hover:border-blue-100"
                                  >
                                    <RotateCcw size={14} /> Restore
                                  </button>
                                )}
                                {isActive && (
                                  <span className="text-xs text-green-600 font-medium px-3 py-1.5">
                                    Current
                                  </span>
                                )}

                                <button
                                  onClick={() => flow.id && handleToggleLock(flow.id, version)}
                                  className={`p-1.5 rounded-md transition-colors ${version.is_locked ? 'text-amber-600 hover:bg-amber-50' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}
                                  title={version.is_locked ? 'Unlock Version' : 'Lock Version'}
                                >
                                  {version.is_locked ? <Lock size={14} /> : <Unlock size={14} />}
                                </button>

                                <button
                                  onClick={() =>
                                    flow.id && handleDeleteVersionClick(flow.id, version.id)
                                  }
                                  disabled={version.is_locked || isActive}
                                  className={`p-1.5 rounded-md transition-colors ${version.is_locked || isActive ? 'text-slate-300 cursor-not-allowed' : 'text-slate-400 hover:text-red-500 hover:bg-red-50'}`}
                                  title={
                                    version.is_locked
                                      ? 'Cannot delete locked version'
                                      : isActive
                                        ? 'Cannot delete active version'
                                        : 'Delete Version'
                                  }
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
