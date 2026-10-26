import React from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import './HardwareReadiness.css';

export const HardwareReadiness: React.FC = () => {
  return (
    <Card
      title="Hardware & AI Runtime Assessment"
      subtitle="Host system resources & Ollama model tier feasibility"
      accent="amber"
      className="hardware-panel"
    >
      <div className="hardware-panel__grid">
        <div className="hardware-panel__spec">
          <span className="hardware-panel__label">Host Processor</span>
          <span className="hardware-panel__val">Intel Core i5-6500</span>
          <span className="hardware-panel__sub">4 Cores, 4 Threads @ 3.20 GHz</span>
        </div>

        <div className="hardware-panel__spec">
          <span className="hardware-panel__label">Physical Memory</span>
          <span className="hardware-panel__val">15.88 GB RAM</span>
          <span className="hardware-panel__sub">~9.5 GB Free Available</span>
        </div>

        <div className="hardware-panel__spec">
          <span className="hardware-panel__label">Graphics Engine</span>
          <span className="hardware-panel__val">Intel HD Graphics 530</span>
          <span className="hardware-panel__sub">Integrated (CPU Inference Mode)</span>
        </div>

        <div className="hardware-panel__spec">
          <span className="hardware-panel__label">PostgreSQL Runtime</span>
          <span className="hardware-panel__val">PostgreSQL 18.6</span>
          <span className="hardware-panel__sub">Service Detected on Host</span>
        </div>
      </div>

      <div className="hardware-panel__assessment">
        <div className="hardware-panel__assessment-header">
          <div className="hardware-panel__assessment-title">
            <span className="hardware-panel__icon">🧠</span>
            <span>Local LLM Feasibility Analysis</span>
          </div>
          <Badge variant="amber" size="sm">
            Phase 1 • No Model Loaded
          </Badge>
        </div>

        <p className="hardware-panel__text">
          Because this workstation operates without a discrete NVIDIA/AMD GPU, local AI inference via Ollama will execute directly on the <strong>Intel Core i5 CPU</strong> and system RAM.
        </p>

        <div className="hardware-panel__tiers">
          <div className="hardware-panel__tier hardware-panel__tier--recommended">
            <div className="hardware-panel__tier-header">
              <Badge variant="emerald" size="sm">Recommended</Badge>
              <span className="hardware-panel__tier-name">Lightweight 3B Models</span>
            </div>
            <p className="hardware-panel__tier-desc">
              e.g. <code>qwen2.5:3b</code> or <code>llama3.2:3b</code> (Q4_K_M ~2.0 GB RAM footprint). Fast CPU token generation (~15-25 tokens/sec).
            </p>
          </div>

          <div className="hardware-panel__tier hardware-panel__tier--caution">
            <div className="hardware-panel__tier-header">
              <Badge variant="amber" size="sm">Feasible with Caution</Badge>
              <span className="hardware-panel__tier-name">Standard 7B/8B Models</span>
            </div>
            <p className="hardware-panel__tier-desc">
              e.g. <code>mistral:7b</code> or <code>llama3.1:8b</code> (Q4_K_M ~4.8 GB RAM footprint). Moderate CPU latency (~5-8 tokens/sec).
            </p>
          </div>

          <div className="hardware-panel__tier hardware-panel__tier--restricted">
            <div className="hardware-panel__tier-header">
              <Badge variant="crimson" size="sm">Not Recommended</Badge>
              <span className="hardware-panel__tier-name">Large 14B+ Models</span>
            </div>
            <p className="hardware-panel__tier-desc">
              Exceeds comfortable free RAM ceiling and causes extreme memory paging and sluggish responses on 4-thread CPU.
            </p>
          </div>
        </div>

        <div className="hardware-panel__boundary-note">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-amber)" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span>
            <strong>Phase 1 Scope:</strong> In accordance with strict boundaries, no LLM models have been downloaded, and no fake AI responses are generated.
          </span>
        </div>
      </div>
    </Card>
  );
};
