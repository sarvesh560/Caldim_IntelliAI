import React from 'react';
import { Badge } from '../ui/Badge';
import './Header.css';

interface HeaderProps {
  apiStatus: 'healthy' | 'unhealthy' | 'unreachable' | 'checking';
  activeTab: 'showroom' | 'consultation' | 'diagnostics';
  onSelectTab: (tab: 'showroom' | 'consultation' | 'diagnostics') => void;
  visitorLabel?: string;
}

export const Header: React.FC<HeaderProps> = ({
  apiStatus,
  activeTab,
  onSelectTab,
  visitorLabel,
}) => {
  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__brand" onClick={() => onSelectTab('showroom')}>
          <div className="header__logo-mark">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-label="CALDIM Logo"
            >
              <path
                d="M12 2L2 7L12 12L22 7L12 2Z"
                stroke="#FFFFFF"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M2 17L12 22L22 17"
                stroke="#FFFFFF"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M2 12L12 17L22 12"
                stroke="#FFFFFF"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeOpacity="0.75"
              />
            </svg>
          </div>
          <div className="header__title-block">
            <div className="header__company-row">
              <span className="header__company">CALDIM</span>
              <span className="header__separator">/</span>
              <span className="header__app-name">IntelliSolve AI</span>
            </div>
            <span className="header__tagline">Industrial AI Consultation Platform</span>
          </div>
        </div>

        {/* View Navigation */}
        <nav className="header__nav">
          <button
            className={`header__nav-btn ${activeTab === 'showroom' ? 'header__nav-btn--active' : ''}`}
            onClick={() => onSelectTab('showroom')}
          >
            Showroom
          </button>
          <button
            className={`header__nav-btn ${activeTab === 'consultation' ? 'header__nav-btn--active' : ''}`}
            onClick={() => onSelectTab('consultation')}
          >
            Consultation Workspace
          </button>
          <button
            className={`header__nav-btn ${activeTab === 'diagnostics' ? 'header__nav-btn--active' : ''}`}
            onClick={() => onSelectTab('diagnostics')}
          >
            Platform Telemetry
          </button>
        </nav>

        <div className="header__meta">
          {visitorLabel && (
            <Badge variant="cyan" size="sm">
              👤 {visitorLabel}
            </Badge>
          )}

          <Badge
            variant={
              apiStatus === 'healthy'
                ? 'emerald'
                : apiStatus === 'checking'
                ? 'amber'
                : 'crimson'
            }
            size="sm"
          >
            {apiStatus === 'healthy'
              ? 'Backend Live'
              : apiStatus === 'checking'
              ? 'Checking...'
              : 'Backend Offline'}
          </Badge>
        </div>
      </div>
    </header>
  );
};
