import React, { useState } from 'react';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import './ShowroomView.css';

interface ShowroomProps {
  onStartConsultation: (initialChallenge: string) => void;
}

interface ChallengePreset {
  id: string;
  category: string;
  productName: string;
  tagline: string;
  problemStatement: string;
  readinessBadge: string;
  industryTag: string;
}

const PRESET_CHALLENGES: ChallengePreset[] = [
  {
    id: 'caltims',
    category: 'Workforce & Operations',
    productName: 'CalTIMS Timesheet & Payroll',
    tagline: 'Sync Weekly Shift Logs Directly to Automated Payroll',
    problemStatement:
      'We operate 3 manufacturing facilities with 350 shift technicians. Reconciling weekly timesheets, OT, and Indian statutory tax/ESI deductions from spreadsheets takes our HR team 4 days every month with recurring audit discrepancies.',
    readinessBadge: 'Preview Ready',
    industryTag: 'Manufacturing',
  },
  {
    id: 'calrims',
    category: 'Recruitment Intelligence',
    productName: 'CalRIMS Talent Parser',
    tagline: 'Semantic Resume Parsing & Skill Matrix Scoring',
    problemStatement:
      'Our engineering recruitment pipeline receives hundreds of multi-page technical CVs weekly. We need an automated semantic parser to qualify candidates against CAD, PLC, and industrial robotics experience without manual screening latency.',
    readinessBadge: 'Preview Ready',
    industryTag: 'Engineering Services',
  },
  {
    id: 'calbuy',
    category: 'Procurement Automation',
    productName: 'CalBUY Requisition Suite',
    tagline: 'Multi-Tier Purchase Approvals & Authority Routing',
    problemStatement:
      'Material purchase requests are delayed in email threads between plant supervisors and finance controllers. We need structured approval routing based on order value, budget center, and authority limits.',
    readinessBadge: 'Preview Ready',
    industryTag: 'Heavy Manufacturing',
  },
  {
    id: 'caltrack',
    category: 'Field Service Operations',
    productName: 'CalTRACK Dispatch Engine',
    tagline: 'Mobile Technician Job Ticketing & Real-Time Tracking',
    problemStatement:
      'Our field technicians service distributed industrial machinery across state highways. Job dispatching is fragmented across phone calls and paper logs, resulting in delayed emergency machine maintenance SLA response times.',
    readinessBadge: 'Preview Ready',
    industryTag: 'Field Logistics',
  },
  {
    id: 'calems',
    category: 'Plant Maintenance',
    productName: 'CalEMS Machine Maintenance',
    tagline: 'Run-Hour Driven Preventive Work Orders',
    problemStatement:
      'Unplanned CNC spindle breakdowns cause expensive production shutdowns. We need automated scheduled servicing work orders triggered directly by machine operating run-hours and calendar intervals.',
    readinessBadge: 'In Development',
    industryTag: 'Automotive & Metalworking',
  },
  {
    id: 'calmisc',
    category: 'Structural Engineering',
    productName: 'CALMISC Takeoff Engine',
    tagline: 'Structural Steel Member Takeoff & Fastener BOM',
    problemStatement:
      'Calculating structural beam weights, protective painting surface areas, and bolt/fastener counts from architectural CAD drawings takes estimators days per tender submission.',
    readinessBadge: 'In Development',
    industryTag: 'Fabrication & Construction',
  },
];

export const ShowroomView: React.FC<ShowroomProps> = ({ onStartConsultation }) => {
  const [customPrompt, setCustomPrompt] = useState('');

  const handleSubmitCustom = (e: React.FormEvent) => {
    e.preventDefault();
    if (customPrompt.trim()) {
      onStartConsultation(customPrompt.trim());
    }
  };

  return (
    <div className="showroom">
      {/* Exhibition Hero */}
      <section className="showroom__hero">
        <div className="showroom__hero-badge-row">
          <Badge variant="purple" size="sm">
            5-Day Industrial Expo Edition
          </Badge>
          <Badge variant="emerald" size="sm">
            Live Consultation Engine Active
          </Badge>
          <Badge variant="neutral" size="sm">
            CALDIM Software Division
          </Badge>
        </div>

        <h1 className="showroom__hero-title">
          Engineering-Grade <span>Industrial AI Consultation</span> & Architecture Discovery
        </h1>

        <p className="showroom__hero-subtitle">
          Explore evidence-grounded system architectures, simulate multi-turn operational roadmaps,
          and discover calibrated enterprise software solutions for manufacturing, workforce, and supply chain bottlenecks.
        </p>

        <form className="showroom__hero-actions" onSubmit={handleSubmitCustom}>
          <div className="showroom__input-bar">
            <input
              type="text"
              className="showroom__input"
              placeholder="Describe your plant, operational, or software challenge..."
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
            />
            <Button type="submit" variant="primary" size="md" disabled={!customPrompt.trim()}>
              Start Consultation →
            </Button>
          </div>
        </form>
      </section>

      {/* Interactive Challenge Cards */}
      <section>
        <div className="showroom__section-header">
          <div>
            <h2 className="showroom__section-title">Common Industrial Challenges</h2>
            <p className="showroom__section-desc">
              Select an operational challenge below to launch an immediate multi-turn consultation.
            </p>
          </div>
        </div>

        <div className="showroom__grid" style={{ marginTop: '24px' }}>
          {PRESET_CHALLENGES.map((preset) => (
            <div
              key={preset.id}
              className="showroom__card"
              onClick={() => onStartConsultation(preset.problemStatement)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onStartConsultation(preset.problemStatement);
                }
              }}
            >
              <div className="showroom__card-top">
                <div className="showroom__card-badges">
                  <Badge variant="cyan" size="sm">
                    {preset.category}
                  </Badge>
                  <Badge variant="neutral" size="sm">
                    {preset.industryTag}
                  </Badge>
                </div>
                <h3 className="showroom__card-title">{preset.productName}</h3>
                <div className="showroom__card-tagline">{preset.tagline}</div>
                <p className="showroom__card-desc">{preset.problemStatement}</p>
              </div>

              <div className="showroom__card-footer">
                <Badge variant={preset.readinessBadge === 'Preview Ready' ? 'emerald' : 'amber'} size="sm">
                  {preset.readinessBadge}
                </Badge>
                <span className="showroom__card-cta">
                  Explore Architecture <span>→</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
