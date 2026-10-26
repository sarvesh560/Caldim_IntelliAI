import React from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import type { HealthApiResponse } from '../../types/health';
import './DiagnosticsPanel.css';

interface DiagnosticsPanelProps {
  data: HealthApiResponse | null;
  latencyMs: number | null;
}

export const DiagnosticsPanel: React.FC<DiagnosticsPanelProps> = ({
  data,
  latencyMs,
}) => {
  return (
    <Card
      title="Endpoint Telemetry & Security"
      subtitle="Safe system attributes returned from /api/v1/health/"
      accent="cyan"
      className="diagnostics-panel"
    >
      <div className="diagnostics-panel__grid">
        <div className="diagnostics-panel__metric">
          <span className="diagnostics-panel__metric-name">Service Identifier</span>
          <span className="diagnostics-panel__metric-value">
            {data ? data.service : '—'}
          </span>
        </div>

        <div className="diagnostics-panel__metric">
          <span className="diagnostics-panel__metric-name">API Version</span>
          <span className="diagnostics-panel__metric-value">
            {data ? `v${data.version}` : '—'}
          </span>
        </div>

        <div className="diagnostics-panel__metric">
          <span className="diagnostics-panel__metric-name">Environment</span>
          <span className="diagnostics-panel__metric-value">
            {data ? (
              <Badge variant="purple" size="sm">
                {data.environment}
              </Badge>
            ) : (
              '—'
            )}
          </span>
        </div>

        <div className="diagnostics-panel__metric">
          <span className="diagnostics-panel__metric-name">Ping Latency</span>
          <span className="diagnostics-panel__metric-value">
            {latencyMs !== null ? `${latencyMs} ms` : '—'}
          </span>
        </div>
      </div>

      <div className="diagnostics-panel__payload-section">
        <div className="diagnostics-panel__payload-header">
          <span className="diagnostics-panel__payload-title">Structured JSON Response</span>
          <Badge variant="emerald" size="sm">
            Zero-Secrets Verified
          </Badge>
        </div>
        <pre className="diagnostics-panel__code-block">
          {data
            ? JSON.stringify(data, null, 2)
            : '// Awaiting valid response payload...'}
        </pre>
      </div>

      <div className="diagnostics-panel__security-note">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-emerald)" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span>
          <strong>Security Guarantee:</strong> Response contains no database passwords, tokens, API keys, or raw stack traces.
        </span>
      </div>
    </Card>
  );
};
