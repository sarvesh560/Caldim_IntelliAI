export type HealthStatus = 'healthy' | 'unhealthy' | 'unreachable' | 'checking';

export interface HealthApiResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  environment: 'development' | 'production';
}

export interface HealthCheckResult {
  state: HealthStatus;
  data: HealthApiResponse | null;
  latencyMs: number | null;
  error: string | null;
  lastChecked: Date | null;
}

export interface HardwareInfo {
  os: string;
  cpu: string;
  totalRamGb: number;
  freeRamGb: number;
  gpu: string;
  hasDiscreteGpu: boolean;
  recommendedLocalModel: string;
  notes: string;
}
