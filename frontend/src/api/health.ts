import { request } from './client';
import type { HealthApiResponse } from '../types/health';

/**
 * Health API service
 * Checks backend connectivity via /api/v1/health/
 */
export const healthApi = {
  async checkHealth(): Promise<{ data: HealthApiResponse; latencyMs: number }> {
    return request<HealthApiResponse>('/api/v1/health/', {
      method: 'GET',
    });
  },
};
