import React from 'react';
import './Footer.css';

export const Footer: React.FC = () => {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <div className="footer__info">
          <span className="footer__title">CALDIM IntelliSolve AI</span>
          <span className="footer__desc">
            Industrial consultation platform foundation • Phase 1
          </span>
        </div>
        <div className="footer__specs">
          <span className="footer__spec-item">
            Workspace: <code>C:\caldim_smartAI\Caldim_IntelliSolve</code>
          </span>
          <span className="footer__spec-item">
            API: <code>/api/v1/health/</code>
          </span>
        </div>
      </div>
    </footer>
  );
};
