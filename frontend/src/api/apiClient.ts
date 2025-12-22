/**
 * Centralized API Client
 * 
 * Provides a unified axios instance with:
 * - Dynamic base URL (Electron support)
 * - JSON:API content type negotiation
 * - Centralized error handling
 */

import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';
import { logError } from './errorHandler';
import { deserializeOne, deserializeMany } from './jsonapi/deserializer';
import type { JSONAPISingleDocument, JSONAPICollectionDocument } from './jsonapi/types';

// Feature flag for JSON:API mode
const USE_JSON_API = import.meta.env.VITE_USE_JSON_API === 'true';

/**
 * Get the API base URL (supports Electron dynamic port)
 */
export async function getBaseUrl(): Promise<string> {
  if ((window as any).electronAPI) {
    const port = await (window as any).electronAPI.getApiPort();
    return `http://localhost:${port}/api`;
  }
  return 'http://localhost:8000/api';
}

/**
 * Create an axios instance with interceptors
 */
export function createApiClient(): AxiosInstance {
  const client = axios.create();

  // Request interceptor - add JSON:API headers if enabled
  client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    // Set base URL dynamically
    if (!config.baseURL) {
      config.baseURL = await getBaseUrl();
    }

    // Add JSON:API headers if feature flag is enabled
    if (USE_JSON_API) {
      config.headers.set('Accept', 'application/vnd.api+json');
      if (config.data && config.method !== 'get') {
        config.headers.set('Content-Type', 'application/vnd.api+json');
      }
    }

    return config;
  });

  // Response interceptor - log errors
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      logError(error, { url: error.config?.url, method: error.config?.method });
      return Promise.reject(error);
    }
  );

  return client;
}

// Singleton API client
let apiClientInstance: AxiosInstance | null = null;

export function getApiClient(): AxiosInstance {
  if (!apiClientInstance) {
    apiClientInstance = createApiClient();
  }
  return apiClientInstance;
}

/**
 * Type-safe response transformer for single resources
 */
export function transformSingleResponse<TAttributes, TDomain extends { id: number }>(
  response: AxiosResponse
): TDomain {
  if (USE_JSON_API) {
    return deserializeOne<TAttributes, TDomain>(response.data as JSONAPISingleDocument<TAttributes>);
  }
  // Legacy format - data is already the domain object
  return response.data as TDomain;
}

/**
 * Type-safe response transformer for collections
 */
export function transformCollectionResponse<TAttributes, TDomain extends { id: number }>(
  response: AxiosResponse
): TDomain[] {
  if (USE_JSON_API) {
    const { items } = deserializeMany<TAttributes, TDomain>(
      response.data as JSONAPICollectionDocument<TAttributes>
    );
    return items;
  }
  // Legacy format - data is already an array
  return response.data as TDomain[];
}

/**
 * Re-export utilities
 */
export { parseApiError } from './errorHandler';
export { USE_JSON_API };
