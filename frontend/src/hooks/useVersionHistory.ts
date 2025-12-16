import { useState } from 'react';
import { toast } from 'sonner';

interface VersionHistoryOptions<TVersion, TRestored> {
    fetchVersions: (id: number) => Promise<TVersion[]>;
    restoreVersion: (id: number, versionId: number) => Promise<TRestored>;
    deleteVersion: (id: number, versionId: number) => Promise<void>;
    deleteVersions?: (id: number, versionIds: number[]) => Promise<void>;
    toggleLock?: (id: number, versionId: number, isLocked: boolean) => Promise<void>;
    onRestoreSuccess?: (restoredItem: TRestored) => void;
}

export function useVersionHistory<TVersion extends { id: number }, TRestored = unknown>(options: VersionHistoryOptions<TVersion, TRestored>) {
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [versions, setVersions] = useState<TVersion[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedVersionIds, setSelectedVersionIds] = useState<Set<number>>(new Set());

    const handleViewVersions = async (id: number) => {
        if (selectedId === id) {
            setSelectedId(null);
            setVersions([]);
            setSelectedVersionIds(new Set());
            return;
        }

        try {
            setSelectedId(id);
            setLoading(true);
            setSelectedVersionIds(new Set());
            const data = await options.fetchVersions(id);
            setVersions(data);
        } catch (error) {
            console.error("Failed to load versions", error);
            toast.error("Failed to load versions");
        } finally {
            setLoading(false);
        }
    };

    const handleRestoreVersion = async (id: number, versionId: number) => {
        if (!confirm("Are you sure you want to restore this version?")) return;
        try {
            const restored = await options.restoreVersion(id, versionId);
            toast.success("Version restored successfully");
            if (options.onRestoreSuccess) {
                options.onRestoreSuccess(restored);
            }
        } catch (error) {
            console.error("Failed to restore version", error);
            toast.error("Failed to restore version");
        }
    };

    const handleDeleteVersion = async (id: number, versionId: number) => {
        if (!confirm(`Are you sure you want to delete version ${versionId}?`)) return;
        try {
            await options.deleteVersion(id, versionId);
            toast.success("Version deleted");
            setVersions(versions.filter(v => v.id !== versionId));
            
            const newSelected = new Set(selectedVersionIds);
            newSelected.delete(versionId);
            setSelectedVersionIds(newSelected);
        } catch (error) {
            console.error("Failed to delete version", error);
            toast.error("Failed to delete version");
        }
    };
    
    const handleBulkDelete = async (id: number) => {
        if (!options.deleteVersions) return;
        if (selectedVersionIds.size === 0) return;
        
        if (!confirm(`Are you sure you want to delete these ${selectedVersionIds.size} versions?`)) return;
        
        try {
            const idsToDelete = Array.from(selectedVersionIds);
            await options.deleteVersions(id, idsToDelete);
            toast.success("Versions deleted");
            setVersions(versions.filter(v => !selectedVersionIds.has(v.id)));
            setSelectedVersionIds(new Set());
        } catch (error) {
            console.error("Failed to delete versions", error);
            toast.error("Failed to delete versions");
        }
    };
    
    const handleToggleLock = async (id: number, version: TVersion & { is_locked?: boolean }) => {
        if (!options.toggleLock) return;
        
        try {
            const newLockState = !version.is_locked;
            await options.toggleLock(id, version.id, newLockState);
            toast.success(`Version ${newLockState ? 'locked' : 'unlocked'}`);
            
            // Update local state
            setVersions(versions.map(v => 
                v.id === version.id ? { ...v, is_locked: newLockState } : v
            ));
        } catch (error) {
            console.error("Failed to toggle lock", error);
            toast.error("Failed to toggle lock");
        }
    };
    
    const toggleVersionSelection = (versionId: number) => {
        const newSelected = new Set(selectedVersionIds);
        if (newSelected.has(versionId)) {
            newSelected.delete(versionId);
        } else {
            newSelected.add(versionId);
        }
        setSelectedVersionIds(newSelected);
    };
    
    const selectAllVersions = (predicate?: (version: TVersion) => boolean) => {
        // You might want to filter out "current" active version if it cannot be deleted?
        // For now, select all loaded versions or filter by predicate.
        const versionsToSelect = predicate ? versions.filter(predicate) : versions;
        setSelectedVersionIds(new Set(versionsToSelect.map(v => v.id)));
    };
    
    const clearSelection = () => {
        setSelectedVersionIds(new Set());
    };

    const reset = () => {
        setSelectedId(null);
        setVersions([]);
        setSelectedVersionIds(new Set());
    };

    return {
        selectedId,
        versions,
        setVersions, // Exposed if needed for manual updates
        loading,
        handleViewVersions,
        handleRestoreVersion,
        handleDeleteVersion,
        // Bulk actions
        selectedVersionIds,
        toggleVersionSelection,
        selectAllVersions,
        clearSelection,
        handleBulkDelete,
        handleToggleLock,
        reset
    };
}
