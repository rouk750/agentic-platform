/**
 * Error Handler Utility
 *
 * Unified error handling for API responses.
 */

import axios from 'axios';
import { isJsonApiError, extractErrorMessages } from './jsonapi';

/**
 * Parse API error to user-friendly message.
 *
 * Handles both JSON:API format and legacy format errors.
 */
export function parseApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;

    // JSON:API format
    if (data && isJsonApiError(data)) {
      return extractErrorMessages(data);
    }

    // Legacy format (FastAPI default)
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      // Validation errors array
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((d: { msg?: string; message?: string }) => d.msg || d.message)
          .filter(Boolean)
          .join('. ');
      }
    }

    // HTTP status message
    if (error.response?.status) {
      const status = error.response.status;
      switch (status) {
        case 400:
          return 'Invalid request';
        case 401:
          return 'Unauthorized';
        case 403:
          return 'Access denied';
        case 404:
          return 'Resource not found';
        case 422:
          return 'Validation error';
        case 429:
          return 'Too many requests. Please try again later.';
        case 500:
          return 'Server error. Please try again.';
        case 502:
          return 'Service unavailable';
        case 503:
          return 'Service temporarily unavailable';
        default:
          return `Error ${status}`;
      }
    }

    // Network error
    if (error.code === 'ERR_NETWORK') {
      return 'Network error. Please check your connection.';
    }

    return error.message || 'An unexpected error occurred';
  }

  // Standard Error
  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred';
}

/**
 * Log error with context for debugging.
 */
export function logError(error: unknown, context?: Record<string, unknown>): void {
  if (axios.isAxiosError(error)) {
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data,
      ...context,
    });
  } else if (error instanceof Error) {
    console.error('Error:', {
      message: error.message,
      stack: error.stack,
      ...context,
    });
  } else {
    console.error('Unknown error:', error, context);
  }
}

/**
 * Create an error handler for async operations.
 *
 * Usage:
 *   const [result, error] = await handleAsync(fetchData());
 *   if (error) { toast.error(error); return; }
 */
export async function handleAsync<T>(promise: Promise<T>): Promise<[T, null] | [null, string]> {
  try {
    const result = await promise;
    return [result, null];
  } catch (error) {
    return [null, parseApiError(error)];
  }
}
