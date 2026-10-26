import React from 'react';
import type { HealthStatus } from '../../types/health';
import './StatusDot.css';

export interface StatusDotProps {
  status: HealthStatus;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
}

export const StatusDot: React.FC<StatusDotProps> = ({
  status,
  size = 'md',
  pulse = true,
}) => {
  return (
    <span className={`status-dot status-dot--${status} status-dot--${size}`}>
      {pulse && <span className="status-dot__pulse" />}
      <span className="status-dot__core" />
    </span>
  );
};
