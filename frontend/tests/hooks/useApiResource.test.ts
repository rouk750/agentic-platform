
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react';
import { useApiResource } from '../../src/hooks/useApiResource';

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock errorHandler
vi.mock('../../src/api/errorHandler', () => ({
  parseApiError: vi.fn((err: Error) => err.message),
}));

interface TestItem {
  id: number;
  name: string;
}

describe('useApiResource', () => {
  const mockApi = {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  };

  const defaultOptions = {
    api: mockApi,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchAll', () => {
    it('should fetch and set items successfully', async () => {
      const mockData = [{ id: 1, name: 'Item 1' }];
      mockApi.getAll.mockResolvedValue(mockData);

      const { result } = renderHook(() => useApiResource(defaultOptions));

      await act(async () => {
        await result.current.fetchAll();
      });

      expect(result.current.items).toEqual(mockData);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle fetch error', async () => {
      const error = new Error('Fetch failed');
      mockApi.getAll.mockRejectedValue(error);

      const { result } = renderHook(() => useApiResource(defaultOptions));

      await act(async () => {
        await result.current.fetchAll();
      });

      expect(result.current.items).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toEqual(error);
    });
  });

  describe('create', () => {
    it('should create item successfully', async () => {
      const newItem = { id: 1, name: 'New Item' };
      mockApi.create.mockResolvedValue(newItem);

      const { result } = renderHook(() => useApiResource(defaultOptions));

      await act(async () => {
        await result.current.create({ name: 'New Item' });
      });

      expect(result.current.items).toContainEqual(newItem);
    });
  });

  describe('update', () => {
    it('should update item successfully', async () => {
      const initialItem = { id: 1, name: 'Old Name' };
      const updatedItem = { id: 1, name: 'New Name' };
      
      mockApi.getAll.mockResolvedValue([initialItem]);
      mockApi.update.mockResolvedValue(updatedItem);

      const { result } = renderHook(() => useApiResource(defaultOptions));

      // Initial load
      await act(async () => {
        await result.current.fetchAll();
      });

      await act(async () => {
        await result.current.update(1, { name: 'New Name' });
      });

      expect(result.current.items[0]).toEqual(updatedItem);
    });
  });

  describe('remove', () => {
    it('should remove item successfully', async () => {
      const item = { id: 1, name: 'Item 1' };
      mockApi.getAll.mockResolvedValue([item]);
      mockApi.delete.mockResolvedValue(undefined);

      const { result } = renderHook(() => useApiResource(defaultOptions));

      await act(async () => {
        await result.current.fetchAll();
      });

      await act(async () => {
        await result.current.remove(1);
      });

      expect(result.current.items).toHaveLength(0);
    });
  });
});
