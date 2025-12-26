/**
 * Tests for JSON:API deserializer
 */

import { describe, it, expect } from 'vitest';
import {
  deserializeOne,
  deserializeMany,
  isJsonApiError,
  extractErrorMessages,
} from '../../../src/api/jsonapi/deserializer';
import type { JSONAPISingleDocument, JSONAPICollectionDocument } from './types';

describe('deserializeOne', () => {
  it('should transform JSON:API resource to domain object', () => {
    const document: JSONAPISingleDocument<{ name: string; value: number }> = {
      data: {
        type: 'items',
        id: '123',
        attributes: {
          name: 'Test Item',
          value: 42,
        },
      },
    };

    const result = deserializeOne<
      typeof document.data.attributes,
      { id: number; name: string; value: number }
    >(document);

    expect(result.id).toBe(123);
    expect(result.name).toBe('Test Item');
    expect(result.value).toBe(42);
  });
});

describe('deserializeMany', () => {
  it('should transform JSON:API collection to domain objects with meta', () => {
    const document: JSONAPICollectionDocument<{ name: string }> = {
      data: [
        { type: 'items', id: '1', attributes: { name: 'Item 1' } },
        { type: 'items', id: '2', attributes: { name: 'Item 2' } },
      ],
      meta: {
        total: 10,
        page: 1,
        per_page: 2,
      },
    };

    const result = deserializeMany<
      (typeof document.data)[0]['attributes'],
      { id: number; name: string }
    >(document);

    expect(result.items).toHaveLength(2);
    expect(result.items[0].id).toBe(1);
    expect(result.items[0].name).toBe('Item 1');
    expect(result.meta.total).toBe(10);
    expect(result.meta.page).toBe(1);
  });

  it('should provide default meta when not present', () => {
    const document: JSONAPICollectionDocument<{ name: string }> = {
      data: [{ type: 'items', id: '1', attributes: { name: 'Item 1' } }],
    };

    const result = deserializeMany<
      (typeof document.data)[0]['attributes'],
      { id: number; name: string }
    >(document);

    expect(result.meta.total).toBe(1);
  });
});

describe('isJsonApiError', () => {
  it('should return true for JSON:API error response', () => {
    const errorResponse = {
      errors: [{ status: '404', code: 'NOT_FOUND', title: 'Not Found' }],
    };

    expect(isJsonApiError(errorResponse)).toBe(true);
  });

  it('should return false for regular response', () => {
    const response = { data: { id: '1' } };
    expect(isJsonApiError(response)).toBe(false);
  });

  it('should return false for null', () => {
    expect(isJsonApiError(null)).toBe(false);
  });
});

describe('extractErrorMessages', () => {
  it('should extract detail messages', () => {
    const errorResponse = {
      errors: [
        {
          status: '400',
          code: 'VALIDATION',
          title: 'Validation Error',
          detail: 'Name is required',
        },
        {
          status: '400',
          code: 'VALIDATION',
          title: 'Validation Error',
          detail: 'Email is invalid',
        },
      ],
    };

    const message = extractErrorMessages(errorResponse);
    expect(message).toBe('Name is required. Email is invalid');
  });

  it('should fall back to title when detail is missing', () => {
    const errorResponse = {
      errors: [{ status: '500', code: 'INTERNAL', title: 'Internal Server Error' }],
    };

    const message = extractErrorMessages(errorResponse);
    expect(message).toBe('Internal Server Error');
  });
});
