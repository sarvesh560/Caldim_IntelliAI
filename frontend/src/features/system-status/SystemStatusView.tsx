import React, { useState } from 'react';
import { useSystemHealth } from '../../hooks/useSystemHealth';
import { SystemStatusCard } from './SystemStatusCard';
import { DiagnosticsPanel } from './DiagnosticsPanel';
import { HardwareReadiness } from './HardwareReadiness';
import { RoadmapOverview } from './RoadmapOverview';
import './SystemStatusView.css';

export const SystemStatusView: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);

  const {
    state,
    data,
    latencyMs,
    error,
    lastChecked,
    isRefreshing,
    retry,
  } = useSystemHealth({
    autoRefresh,
    intervalMs: 15000,
  });

  return (
    <div className="status-view">
      <div className="status-view__container">
        {/* Intro Hero */}
        <section className="status-view__intro">
          <div className="status-view__intro-tag">Phase 1: Architecture & Telemetry</div>
          <h1 className="status-view__intro-title">
            CALDIM IntelliSolve AI <span className="status-view__gradient-text">System Status</span>
          </h1>
          <p className="status-view__intro-lead">
            Industrial consultation platform foundation. Verifying end-to-end communication
            between the React TypeScript frontend and the Django REST Framework backend API.
          </p>
        </section>

        {/* Primary Status Card */}
        <section className="status-view__section">
          <SystemStatusCard
            status={state}
            data={data}
            latencyMs={latencyMs}
            error={error}
            lastChecked={lastChecked}
            isRefreshing={isRefreshing}
            onRetry={retry}
            autoRefresh={autoRefresh}
            onToggleAutoRefresh={setAutoRefresh}
          />
        </section>

        {/* Technical Diagnostics & Hardware Analysis */}
        <section className="status-view__grid-two">
          <DiagnosticsPanel data={data} latencyMs={latencyMs} />
          <HardwareReadiness />
        </section>

        {/* Roadmap Overview */}
        <section className="status-view__section">
          <RoadmapOverview />
        </section>
      </div>
    </div>
  );
};
