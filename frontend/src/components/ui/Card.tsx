import React from 'react';
import './Card.css';

export interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  headerAction?: React.ReactNode;
  accent?: 'cyan' | 'teal' | 'emerald' | 'amber' | 'crimson' | 'purple' | 'none';
  interactive?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  headerAction,
  accent = 'none',
  interactive = false,
  className = '',
}) => {
  const hasHeader = title || subtitle || headerAction;

  return (
    <div
      className={`card card--accent-${accent} ${interactive ? 'card--interactive' : ''} ${className}`}
    >
      {hasHeader && (
        <div className="card__header">
          <div className="card__titles">
            {title && <h3 className="card__title">{title}</h3>}
            {subtitle && <p className="card__subtitle">{subtitle}</p>}
          </div>
          {headerAction && <div className="card__action">{headerAction}</div>}
        </div>
      )}
      <div className="card__content">{children}</div>
    </div>
  );
};
