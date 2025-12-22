
/**
 * Tests for error handler utility
 */

import { describe, it, expect, vi } from 'vitest';
import { parseApiError, handleAsync } from "../../src/api/errorHandler";
import type { AxiosError } from 'axios';

// Mock axios
vi.mock('axios', async () => {
  const actual = await vi.importActual('axios');
  return {
    ...actual,
    isAxiosError: (error: unknown): error is AxiosError => {
      return (
        typeof error === 'object' &&
        error !== null &&
        'isAxiosError' in error &&
        (error as AxiosError).isAxiosError === true
      );
    },
  };
});

function createAxiosError(
  status: number,
  data?: unknown,
  code?: string
): AxiosError {
  const error = new Error('Request failed') as AxiosError;
  error.isAxiosError = true;
  error.config = { url: '/test', method: 'get' } as AxiosError['config'];
  error.response = {
    status,
    data,
    statusText: 'Error',
    headers: {},
    config: error.config!,
  } as AxiosError['response'];
  if (code) {
    error.code = code;
  }
  return error;
}

describe('parseApiError', () => {
  it('should parse JSON:API error format', () => {
    const error = createAxiosError(400, {
      errors: [
        { status: '400', code: 'VALIDATION', title: 'Validation Error', detail: 'Name is required' },
      ],
    });

    const message = parseApiError(error);
    expect(message).toBe('Name is required');
  });

  it('should parse legacy FastAPI detail string', () => {
    const error = createAxiosError(404, { detail: 'Flow not found' });

    const message = parseApiError(error);
    expect(message).toBe('Flow not found');
  });

  it('should parse FastAPI validation error array', () => {
    const error = createAxiosError(422, {
      detail: [
        { msg: 'field required', loc: ['body', 'name'] },
        { msg: 'invalid email', loc: ['body', 'email'] },
      ],
    });

    const message = parseApiError(error);
    expect(message).toBe('field required. invalid email');
  });

  it('should return status message for unknown error', () => {
    const error = createAxiosError(500, {});

    const message = parseApiError(error);
    expect(message).toBe('Server error. Please try again.');
  });

  it('should handle network errors', () => {
    const error = createAxiosError(0, undefined, 'ERR_NETWORK');

    const message = parseApiError(error);
    expect(message).toBe('Network error. Please check your connection.');
  });

  it('should handle standard Error', () => {
    const error = new Error('Something went wrong');

    const message = parseApiError(error);
    expect(message).toBe('Something went wrong');
  });

  it('should handle unknown error types', () => {
    const message = parseApiError('unknown error');
    expect(message).toBe('An unexpected error occurred');
  });
});

describe('handleAsync', () => {
  it('should return result on success', async () => {
    const promise = Promise.resolve({ data: 'test' });

    const [result, error] = await handleAsync(promise);

    expect(result).toEqual({ data: 'test' });
    expect(error).toBeNull();
  });

  it('should return error message on failure', async () => {
    const axiosError = createAxiosError(404, { detail: 'Not found' });
    const promise = Promise.reject(axiosError);

    const [result, error] = await handleAsync(promise);

    expect(result).toBeNull();
    expect(error).toBe('Not found');
  });
});
