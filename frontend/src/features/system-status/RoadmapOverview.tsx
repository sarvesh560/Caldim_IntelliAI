import React from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import './RoadmapOverview.css';

export const RoadmapOverview: React.FC = () => {
  const phases = [
    {
      num: '01',
      title: 'Foundation & Telemetry',
      status: 'Completed',
      variant: 'cyan' as const,
      active: true,
      items: [
        'React + TypeScript (Strict) + Vite frontend setup',
        'Django + Django REST Framework + CORS backend architecture',
        'Safe health check endpoint (/api/v1/health/) with zero leaks',
        'Hardware & local AI runtime capacity profiling',
        'Environment-based PostgreSQL configuration readiness',
      ],
    },
    {
      num: '02',
      title: 'PostgreSQL & Visitor Data',
      status: 'Phase 2 Complete',
      variant: 'emerald' as const,
      active: true,
      items: [
        'PostgreSQL 18 database connected as primary engine',
        'Visitor professional profile model with UUID & audit timestamps',
        'Explicit GDPR/Privacy consent records with atomic revocation',
        'Consultation session model with operational metadata filtering',
        'Protected visitor endpoints with token ownership verification',
      ],
    },
    {
      num: '03',
      title: 'AI Consultation & Retrieval',
      status: 'Pending Approval',
      variant: 'neutral' as const,
      active: false,
      items: [
        'Ollama local runtime connector (Qwen 2.5 3B / Llama 3.2 3B)',
        'Provider-agnostic AI interface (local Ollama + cloud LLMs)',
        'CALDIM product catalog & verified technical spec ingestion',
        'Role-adaptive industrial prompt templates',
      ],
    },
    {
      num: '04',
      title: 'Proposals, ROI & Staff Dashboard',
      status: 'Roadmap',
      variant: 'neutral' as const,
      active: false,
      items: [
        'Industrial problem diagnosis and ROI calculation engine',
        'Exportable consultation summary and proposal generation',
        'Staff lead management, follow-up queues, and conversion metrics',
      ],
    },
  ];

  return (
    <Card
      title="Platform Implementation Roadmap"
      subtitle="Phase 2 PostgreSQL and visitor persistence completed — awaiting approval before Phase 3 AI integration"
      accent="purple"
      className="roadmap-panel"
    >
      <div className="roadmap-panel__list">
        {phases.map((phase) => (
          <div
            key={phase.num}
            className={`roadmap-panel__item ${
              phase.active ? 'roadmap-panel__item--active' : ''
            }`}
          >
            <div className="roadmap-panel__item-header">
              <div className="roadmap-panel__num-wrap">
                <span className="roadmap-panel__num">{phase.num}</span>
                <span className="roadmap-panel__item-title">{phase.title}</span>
              </div>
              <Badge variant={phase.variant} size="sm">
                {phase.status}
              </Badge>
            </div>

            <ul className="roadmap-panel__checklist">
              {phase.items.map((item, idx) => (
                <li key={idx} className="roadmap-panel__check-item">
                  <span className="roadmap-panel__check-icon">
                    {phase.active ? '✓' : '○'}
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Card>
  );
};
