import React from 'react';
import { Card } from '../../components/ui/Card';
import { StatusDot } from '../../components/ui/StatusDot';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { API_CONFIG } from '../../api/client';
import type { HealthStatus, HealthApiResponse } from '../../types/health';
import './SystemStatusCard.css';

interface SystemStatusCardProps {
  status: HealthStatus;
  data: HealthApiResponse | null;
  latencyMs: number | null;
  error: string | null;
  lastChecked: Date | null;
  isRefreshing: boolean;
  onRetry: () => void;
  autoRefresh: boolean;
  onToggleAutoRefresh: (val: boolean) => void;
}

export const SystemStatusCard: React.FC<SystemStatusCardProps> = ({
  status,
  data,
  latencyMs,
  error,
  lastChecked,
  isRefreshing,
  onRetry,
  autoRefresh,
  onToggleAutoRefresh,
}) => {
  const isHealthy = status === 'healthy';
  const isChecking = status === 'checking';
  const isUnreachable = status === 'unreachable';

  const accentColor = isHealthy ? 'emerald' : isChecking ? 'amber' : 'crimson';

  return (
    <Card
      accent={accentColor}
      className="status-card"
      headerAction={
        <div className="status-card__controls">
          <label className="status-card__toggle-label">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => onToggleAutoRefresh(e.target.checked)}
              className="status-card__checkbox"
            />
            <span className="status-card__toggle-text">Live Polling (15s)</span>
          </label>
          <Button
            variant={isHealthy ? 'secondary' : 'primary'}
            size="sm"
            onClick={onRetry}
            isLoading={isRefreshing}
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
            }
          >
            {isHealthy ? 'Recheck' : 'Retry Connection'}
          </Button>
        </div>
      }
    >
      <div className="status-card__hero">
        <div className="status-card__indicator-box">
          <StatusDot status={status} size="lg" />
        </div>

        <div className="status-card__headline-group">
          <div className="status-card__badge-row">
            <Badge
              variant={isHealthy ? 'emerald' : isChecking ? 'amber' : 'crimson'}
              size="md"
            >
              {isHealthy ? 'SYSTEM OPERATIONAL' : isChecking ? 'CONNECTING...' : 'DISCONNECTED'}
            </Badge>

            {latencyMs !== null && (
              <Badge variant="cyan" size="sm">
                {latencyMs}ms Latency
              </Badge>
            )}

            {data?.environment && (
              <Badge variant="purple" size="sm">
                {data.environment}
              </Badge>
            )}
          </div>

          <h2 className="status-card__title">
            {isHealthy && 'Backend API Health Endpoint Verified'}
            {isChecking && 'Querying Django REST Framework Health Endpoint...'}
            {isUnreachable && 'Backend Health Endpoint Unreachable'}
          </h2>

          <p className="status-card__description">
            {isHealthy &&
              `Successfully established zero-trust HTTP handshake with Django API at ${API_CONFIG.baseUrl}/api/v1/health/. Responses are safe and unauthenticated.`}
            {isChecking &&
              `Dispatching health probe to configured base URL: ${API_CONFIG.baseUrl}/api/v1/health/...`}
            {isUnreachable &&
              `Failed to reach backend endpoint at ${API_CONFIG.baseUrl}/api/v1/health/. Please ensure the backend server is running.`}
          </p>
        </div>
      </div>

      {isUnreachable && error && (
        <div className="status-card__error-box">
          <div className="status-card__error-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-crimson)" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="status-card__error-title">Connection Diagnosis</span>
          </div>
          <p className="status-card__error-message">{error}</p>
          <div className="status-card__troubleshooting">
            <strong>PowerShell Quick Start:</strong>
            <code>cd backend; .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000</code>
          </div>
        </div>
      )}

      <div className="status-card__footer">
        <div className="status-card__meta-item">
          <span className="status-card__meta-label">Configured Target:</span>
          <code className="status-card__meta-code">{API_CONFIG.baseUrl}/api/v1/health/</code>
        </div>
        <div className="status-card__meta-item">
          <span className="status-card__meta-label">Last Ping:</span>
          <span className="status-card__meta-val">
            {lastChecked ? lastChecked.toLocaleTimeString() : 'Never'}
          </span>
        </div>
      </div>
    </Card>
  );
};
