/**
 * Centralized Typed API Client
 * Configured with configurable backend base URL and structured error handling.
 */

export interface ApiClientConfig {
  baseUrl: string;
  timeoutMs: number;
}

export class ApiError extends Error {
  public readonly status?: number;
  public readonly code: string;

  constructor(message: string, status?: number, code: string = 'API_ERROR') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export const API_CONFIG: ApiClientConfig = {
  baseUrl: (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') || 'http://127.0.0.1:8000',
  timeoutMs: 8000,
};

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ data: T; latencyMs: number }> {
  const url = `${API_CONFIG.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const startTime = performance.now();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);
    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status} (${response.statusText})`;
      try {
        const errorJson = await response.json();
        if (errorJson && typeof errorJson === 'object' && 'detail' in errorJson) {
          errorMessage = String(errorJson.detail);
        } else if (errorJson && typeof errorJson === 'object' && 'error' in errorJson) {
          errorMessage = String(errorJson.error);
        }
      } catch {
        // Fall back to default status text if not JSON
      }
      throw new ApiError(errorMessage, response.status, 'HTTP_ERROR');
    }

    const data = (await response.json()) as T;
    return { data, latencyMs };
  } catch (error: unknown) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(
        `Connection timed out after ${API_CONFIG.timeoutMs}ms. Verify backend is running at ${API_CONFIG.baseUrl}.`,
        0,
        'TIMEOUT_ERROR'
      );
    }

    const message = error instanceof Error ? error.message : 'Unknown network failure';
    throw new ApiError(
      `Cannot connect to backend at ${API_CONFIG.baseUrl}. Ensure Django server is running. (${message})`,
      0,
      'NETWORK_FAILURE'
    );
  }
}
