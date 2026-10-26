import { useState, useEffect, useCallback, useRef } from 'react';
import { healthApi } from '../api/health';
import type { HealthCheckResult } from '../types/health';

interface UseSystemHealthOptions {
  autoRefresh?: boolean;
  intervalMs?: number;
}

export function useSystemHealth(options: UseSystemHealthOptions = {}) {
  const { autoRefresh = false, intervalMs = 15000 } = options;

  const [state, setState] = useState<HealthCheckResult>({
    state: 'checking',
    data: null,
    latencyMs: null,
    error: null,
    lastChecked: null,
  });

  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const isMounted = useRef<boolean>(true);

  const performCheck = useCallback(async (isManual = false) => {
    if (isManual) {
      setIsRefreshing(true);
    } else {
      setState((prev) => ({ ...prev, state: 'checking' }));
    }

    try {
      const { data, latencyMs } = await healthApi.checkHealth();
      if (!isMounted.current) return;

      setState({
        state: data.status === 'healthy' ? 'healthy' : 'unhealthy',
        data,
        latencyMs,
        error: null,
        lastChecked: new Date(),
      });
    } catch (err: unknown) {
      if (!isMounted.current) return;
      const errorMessage = err instanceof Error ? err.message : 'Unknown connectivity failure';

      setState((prev) => ({
        ...prev,
        state: 'unreachable',
        error: errorMessage,
        latencyMs: null,
        lastChecked: new Date(),
      }));
    } finally {
      if (isMounted.current) {
        setIsRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;
    performCheck(false);

    let timer: number | null = null;
    if (autoRefresh && intervalMs > 0) {
      timer = window.setInterval(() => {
        performCheck(false);
      }, intervalMs);
    }

    return () => {
      isMounted.current = false;
      if (timer !== null) {
        clearInterval(timer);
      }
    };
  }, [autoRefresh, intervalMs, performCheck]);

  return {
    ...state,
    isRefreshing,
    retry: () => performCheck(true),
  };
}
