/**
 * JSON:API Deserializer
 * 
 * Transforms JSON:API responses to domain objects.
 */

import type {
  JSONAPISingleDocument,
  JSONAPICollectionDocument,
  JSONAPIMeta,
} from './types';

/**
 * Extract domain object from JSON:API single resource document.
 */
export function deserializeOne<TAttributes, TDomain extends { id: number }>(
  document: JSONAPISingleDocument<TAttributes>
): TDomain {
  const resource = document.data;
  return {
    id: parseInt(resource.id, 10),
    ...resource.attributes,
  } as unknown as TDomain;
}

/**
 * Extract domain objects from JSON:API collection document.
 */
export function deserializeMany<TAttributes, TDomain extends { id: number }>(
  document: JSONAPICollectionDocument<TAttributes>
): {
  items: TDomain[];
  meta: JSONAPIMeta;
} {
  const items = document.data.map((resource) => ({
    id: parseInt(resource.id, 10),
    ...resource.attributes,
  })) as unknown as TDomain[];

  return {
    items,
    meta: document.meta || { total: items.length, page: 1, per_page: items.length },
  };
}

/**
 * Check if response is a JSON:API error response.
 */
export function isJsonApiError(data: unknown): boolean {
  return (
    typeof data === 'object' &&
    data !== null &&
    'errors' in data &&
    Array.isArray((data as { errors: unknown[] }).errors)
  );
}

/**
 * Extract error messages from JSON:API error response.
 */
export function extractErrorMessages(data: { errors: Array<{ detail?: string; title: string }> }): string {
  return data.errors
    .map((e) => e.detail || e.title)
    .filter(Boolean)
    .join('. ');
}
