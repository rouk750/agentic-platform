import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { parseApiError } from '../api/errorHandler';

interface ApiResourceOptions<T, TCreate, TUpdate> {
  api: {
    getAll: () => Promise<T[]>;
    create: (data: TCreate) => Promise<T>;
    update: (id: number, data: TUpdate) => Promise<T>;
    delete: (id: number) => Promise<void>;
  };
  onBeforeCreate?: (data: TCreate) => void;
  onAfterCreate?: (item: T) => void;
  onBeforeUpdate?: (id: number, data: TUpdate) => void;
  onAfterUpdate?: (item: T) => void;
  onBeforeDelete?: (id: number) => void;
  onAfterDelete?: (id: number) => void;
  messages?: {
    createSuccess?: string;
    updateSuccess?: string;
    deleteSuccess?: string;
    loadError?: string;
    createError?: string;
    updateError?: string;
    deleteError?: string;
  };
}

export function useApiResource<
  T extends { id?: number },
  TCreate = Omit<T, 'id'>,
  TUpdate = Partial<T>,
>(options: ApiResourceOptions<T, TCreate, TUpdate>) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Destructure options to use in deps array safely
  // Note: The caller must ensure these function references are stable (e.g. templateApi methods are stable imports) or memoized.
  const {
    api,
    onBeforeCreate,
    onAfterCreate,
    onBeforeUpdate,
    onAfterUpdate,
    onBeforeDelete,
    onAfterDelete,
    messages: customMessages,
  } = options;

  const messages = {
    createSuccess: 'Created successfully',
    updateSuccess: 'Updated successfully',
    deleteSuccess: 'Deleted successfully',
    loadError: 'Failed to load items',
    createError: 'Failed to create item',
    updateError: 'Failed to update item',
    deleteError: 'Failed to delete item',
    ...customMessages,
  };

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAll();
      setItems(data);
    } catch (err) {
      const error = err as Error;
      console.error(messages.loadError, error);
      setError(error);
      toast.error(parseApiError(err));
    } finally {
      setLoading(false);
    }
  }, [api, messages.loadError]);

  const create = useCallback(
    async (data: TCreate) => {
      try {
        onBeforeCreate?.(data);
        const newItem = await api.create(data);
        setItems((prev) => [newItem, ...prev]);
        toast.success(messages.createSuccess);
        onAfterCreate?.(newItem);
        return newItem;
      } catch (err) {
        const error = err as Error;
        console.error(messages.createError, error);
        toast.error(parseApiError(err));
        throw error;
      }
    },
    [api, messages.createSuccess, messages.createError, onBeforeCreate, onAfterCreate]
  );

  const update = useCallback(
    async (id: number, data: TUpdate) => {
      try {
        onBeforeUpdate?.(id, data);
        const updatedItem = await api.update(id, data);
        setItems((prev) => prev.map((item) => (item.id === id ? updatedItem : item)));
        toast.success(messages.updateSuccess);
        onAfterUpdate?.(updatedItem);
        return updatedItem;
      } catch (err) {
        const error = err as Error;
        console.error(messages.updateError, error);
        toast.error(parseApiError(err));
        throw error;
      }
    },
    [api, messages.updateSuccess, messages.updateError, onBeforeUpdate, onAfterUpdate]
  );

  const remove = useCallback(
    async (id: number) => {
      try {
        onBeforeDelete?.(id);
        await api.delete(id);
        setItems((prev) => prev.filter((item) => item.id !== id));
        toast.success(messages.deleteSuccess);
        onAfterDelete?.(id);
      } catch (err) {
        const error = err as Error;
        console.error(messages.deleteError, error);
        toast.error(parseApiError(err));
        throw error;
      }
    },
    [api, messages.deleteSuccess, messages.deleteError, onBeforeDelete, onAfterDelete]
  );

  return {
    items,
    setItems,
    loading,
    error,
    fetchAll,
    create,
    update,
    remove,
  };
}
