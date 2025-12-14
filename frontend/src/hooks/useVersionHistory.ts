import { useState } from 'react';
import { toast } from 'sonner';

interface VersionHistoryOptions<TVersion, TRestored> {
    fetchVersions: (id: number) => Promise<TVersion[]>;
    restoreVersion: (id: number, versionId: number) => Promise<TRestored>;
    deleteVersion: (id: number, versionId: number) => Promise<void>;
    onRestoreSuccess?: (restoredItem: TRestored) => void;
}

export function useVersionHistory<TVersion extends { id: number }, TRestored = unknown>(options: VersionHistoryOptions<TVersion, TRestored>) {
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [versions, setVersions] = useState<TVersion[]>([]);
    const [loading, setLoading] = useState(false);

    const handleViewVersions = async (id: number) => {
        if (selectedId === id) {
            setSelectedId(null);
            setVersions([]);
            return;
        }

        try {
            setSelectedId(id);
            setLoading(true);
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
        if (!confirm("Are you sure you want to delete this version?")) return;
        try {
            await options.deleteVersion(id, versionId);
            toast.success("Version deleted");
            setVersions(versions.filter(v => v.id !== versionId));
        } catch (error) {
            console.error("Failed to delete version", error);
            toast.error("Failed to delete version");
        }
    };

    const reset = () => {
        setSelectedId(null);
        setVersions([]);
    };

    return {
        selectedId,
        versions,
        setVersions, // Exposed if needed for manual updates
        loading,
        handleViewVersions,
        handleRestoreVersion,
        handleDeleteVersion,
        reset
    };
}
