import React, { useState, useEffect, useRef } from 'react';
import { visitorApi } from '../../api/visitor';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import type {
  VisitorProfile,
  ConsentCategory,
  ConsentStatus,
} from '../../types/visitor';
import './ConversationalOnboarding.css';

interface ConversationalOnboardingProps {
  token: string;
  visitor: VisitorProfile;
  onUpdateProfile: (data: {
    displayName?: string;
    email?: string;
    phone?: string;
    profession?: string;
    companyName?: string;
    industry?: string;
    department?: string;
    responsibilities?: string;
  }) => Promise<VisitorProfile | undefined>;
  onComplete: () => void;
  pendingChallenge?: string;
}

interface StepConfig {
  key:
    | 'display_name'
    | 'email'
    | 'phone'
    | 'profession'
    | 'company_name'
    | 'industry'
    | 'department';
  label: string;
  prompt: (name?: string) => string;
  placeholder: string;
  inputType: 'text' | 'email' | 'tel';
  validate: (val: string) => string | null;
}

const ONBOARDING_STEPS: StepConfig[] = [
  {
    key: 'display_name',
    label: 'Full Name',
    prompt: () =>
      "Welcome to CALDIM IntelliSolve AI. To provide an engineering-grade architectural consultation tailored to your organization, let's begin with your full name. What is your full name?",
    placeholder: 'e.g. Elena Vance or Marcus Thorne',
    inputType: 'text',
    validate: (val: string) => {
      const clean = val.trim();
      if (clean.length < 2) return 'Please enter your full name (at least 2 characters).';
      return null;
    },
  },
  {
    key: 'email',
    label: 'Email Address',
    prompt: (name?: string) =>
      `Nice to meet you${name ? `, ${name}` : ''}. What is your official business email address? We will use this to deliver your solution blueprints and architecture proposals.`,
    placeholder: 'e.g. elena.vance@company.com',
    inputType: 'email',
    validate: (val: string) => {
      const clean = val.trim();
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(clean)) {
        return 'Please enter a valid business email address (e.g. name@organization.com).';
      }
      return null;
    },
  },
  {
    key: 'phone',
    label: 'Phone Number with Country Code',
    prompt: () =>
      'Thank you. What is your contact phone number, including your country code? (e.g. +91 98765 43210 or +1 555 019 2834)',
    placeholder: 'e.g. +91 98765 43210 or +1 555 019 2834',
    inputType: 'tel',
    validate: (val: string) => {
      const clean = val.trim();
      const phoneRegex = /^\+?[0-9\s\-().]{6,25}$/;
      if (!phoneRegex.test(clean)) {
        return 'Please enter a valid phone number with country code (e.g. +1 555 019 2834 or +91 98765 43210).';
      }
      return null;
    },
  },
  {
    key: 'profession',
    label: 'Profession / Job Title',
    prompt: () =>
      'What is your current profession or job title? (e.g. VP of Operations, Plant Manager, Head of Supply Chain, Solution Architect)',
    placeholder: 'e.g. VP of Manufacturing Technology',
    inputType: 'text',
    validate: (val: string) => {
      if (val.trim().length < 2) return 'Please specify your job title or professional role.';
      return null;
    },
  },
  {
    key: 'company_name',
    label: 'Company Where Applicable',
    prompt: () =>
      "What company or manufacturing organization do you represent? If you are an independent consultant or researcher, simply state 'Independent'.",
    placeholder: 'e.g. Vance Precision Industries or Independent',
    inputType: 'text',
    validate: (val: string) => {
      if (val.trim().length < 2) return 'Please enter your organization name or Independent.';
      return null;
    },
  },
  {
    key: 'industry',
    label: 'Industry / Business Type',
    prompt: () =>
      'What is your primary industry or business sector? (e.g. Precision Machining, Automotive Tier 1, Pharmaceuticals, Heavy Fabrication, Logistics)',
    placeholder: 'e.g. Aerospace & Precision Machining',
    inputType: 'text',
    validate: (val: string) => {
      if (val.trim().length < 2) return 'Please specify your industry sector.';
      return null;
    },
  },
  {
    key: 'department',
    label: 'Department & Responsibilities',
    prompt: () =>
      'Finally, what is your primary department and operational responsibilities? (e.g. Operations Engineering, managing factory shift scheduling, machine telemetry, and payroll automation)',
    placeholder: 'e.g. Operations Engineering, plant workforce management',
    inputType: 'text',
    validate: (val: string) => {
      if (val.trim().length < 3)
        return 'Please describe your department and key responsibilities.';
      return null;
    },
  },
];

interface ChatMessage {
  id: string;
  sender: 'assistant' | 'user';
  text: string;
  isError?: boolean;
}

export const ConversationalOnboarding: React.FC<ConversationalOnboardingProps> = ({
  token,
  visitor,
  onUpdateProfile,
  onComplete,
  pendingChallenge,
}) => {
  // Determine starting step based on already filled profile attributes
  const determineInitialStep = (): number => {
    for (let i = 0; i < ONBOARDING_STEPS.length; i++) {
      const step = ONBOARDING_STEPS[i];
      const val = visitor[step.key as keyof VisitorProfile];
      if (!val || (typeof val === 'string' && val.trim() === '')) {
        return i;
      }
    }
    return ONBOARDING_STEPS.length; // Step 7 means ready for confirmation
  };

  const [currentStepIndex, setCurrentStepIndex] = useState<number>(determineInitialStep);
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [editingFieldKey, setEditingFieldKey] = useState<string | null>(null);

  // Consent states for step 8 confirmation
  const [consentEssential] = useState<boolean>(true);
  const [consentProposals, setConsentProposals] = useState<boolean>(true);
  const [consentAnalytics, setConsentAnalytics] = useState<boolean>(false);
  const [consentMarketing, setConsentMarketing] = useState<boolean>(false);
  const [consentSubmitting, setConsentSubmitting] = useState<boolean>(false);
  const [consentError, setConsentError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Build conversational message thread
  useEffect(() => {
    const thread: ChatMessage[] = [];

    // Replay filled steps
    for (let i = 0; i < currentStepIndex && i < ONBOARDING_STEPS.length; i++) {
      const step = ONBOARDING_STEPS[i];
      const answer = visitor[step.key as keyof VisitorProfile];
      thread.push({
        id: `q-${i}`,
        sender: 'assistant',
        text: step.prompt(visitor.display_name),
      });
      if (answer) {
        thread.push({
          id: `a-${i}`,
          sender: 'user',
          text: String(answer),
        });
      }
    }

    // Add prompt for current step
    if (currentStepIndex < ONBOARDING_STEPS.length) {
      const currentStep = ONBOARDING_STEPS[currentStepIndex];
      thread.push({
        id: `q-${currentStepIndex}`,
        sender: 'assistant',
        text: currentStep.prompt(visitor.display_name),
      });
    }

    setMessages(thread);
  }, [currentStepIndex]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    inputRef.current?.focus();
  }, [messages, currentStepIndex]);

  const handleStepSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = inputValue.trim();
    if (!clean || isSubmitting) return;

    const currentStep = ONBOARDING_STEPS[currentStepIndex];
    if (!currentStep) return;

    // Validate
    const errorMsg = currentStep.validate(clean);
    if (errorMsg) {
      setMessages((prev) => [
        ...prev,
        { id: `user-attempt-${Date.now()}`, sender: 'user', text: clean },
        { id: `err-${Date.now()}`, sender: 'assistant', text: errorMsg, isError: true },
      ]);
      setInputValue('');
      return;
    }

    setIsSubmitting(true);
    try {
      // Map step key to patch payload
      const patchData: Record<string, string> = {};
      if (currentStep.key === 'display_name') patchData.displayName = clean;
      if (currentStep.key === 'email') patchData.email = clean;
      if (currentStep.key === 'phone') patchData.phone = clean;
      if (currentStep.key === 'profession') patchData.profession = clean;
      if (currentStep.key === 'company_name') patchData.companyName = clean;
      if (currentStep.key === 'industry') patchData.industry = clean;
      if (currentStep.key === 'department') {
        patchData.department = clean.slice(0, 150);
        patchData.responsibilities = clean;
      }

      await onUpdateProfile(patchData);

      setInputValue('');

      if (editingFieldKey) {
        // Returned from editing a single field
        setEditingFieldKey(null);
        setCurrentStepIndex(ONBOARDING_STEPS.length);
      } else {
        setCurrentStepIndex((prev) => prev + 1);
      }
    } catch (err: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-net-${Date.now()}`,
          sender: 'assistant',
          text: 'Encountered an issue saving your response. Please verify and retry.',
          isError: true,
        },
      ]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditField = (stepIndex: number) => {
    setEditingFieldKey(ONBOARDING_STEPS[stepIndex].key);
    setCurrentStepIndex(stepIndex);
  };

  const handleConfirmProfileAndConsents = async () => {
    if (!consentEssential) {
      setConsentError('Essential service processing consent is required to start a consultation.');
      return;
    }

    setConsentSubmitting(true);
    setConsentError(null);

    try {
      // Record all 4 explicit consents
      await visitorApi.recordConsent(
        visitor.id,
        token,
        'essential' as ConsentCategory,
        'granted' as ConsentStatus
      );

      await visitorApi.recordConsent(
        visitor.id,
        token,
        'proposal_delivery' as ConsentCategory,
        (consentProposals ? 'granted' : 'denied') as ConsentStatus
      );

      await visitorApi.recordConsent(
        visitor.id,
        token,
        'analytics' as ConsentCategory,
        (consentAnalytics ? 'granted' : 'denied') as ConsentStatus
      );

      await visitorApi.recordConsent(
        visitor.id,
        token,
        'marketing' as ConsentCategory,
        (consentMarketing ? 'granted' : 'denied') as ConsentStatus
      );

      // Create consultation session
      await visitorApi.createSession(visitor.id, token, {
        kiosk_source: 'first_contact_onboarding',
        timestamp: new Date().toISOString(),
      });

      // Complete onboarding and transition to consultation
      onComplete();
    } catch (err: unknown) {
      setConsentError('Failed to record consent preferences. Please retry.');
    } finally {
      setConsentSubmitting(false);
    }
  };

  const currentStep = ONBOARDING_STEPS[currentStepIndex];
  const isConfirmationStep = currentStepIndex >= ONBOARDING_STEPS.length;

  return (
    <div className="onboarding">
      {/* Top Progress Bar */}
      <div className="onboarding__progress-header">
        <div className="onboarding__progress-info">
          <Badge variant="cyan" size="sm">
            Step 1 of 2: Mandatory First-Contact Calibration
          </Badge>
          <span className="onboarding__progress-counter">
            {isConfirmationStep
              ? 'Profile Calibration Complete — Awaiting Confirmation'
              : `Question ${currentStepIndex + 1} of ${ONBOARDING_STEPS.length}`}
          </span>
        </div>

        <div className="onboarding__progress-track">
          <div
            className="onboarding__progress-fill"
            style={{
              width: `${Math.min(100, ((currentStepIndex) / ONBOARDING_STEPS.length) * 100)}%`,
            }}
          />
        </div>
      </div>

      {/* Main Chat Thread */}
      <div className="onboarding__chat-col">
        <div className="onboarding__messages-list">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`onboarding__msg onboarding__msg--${msg.sender} ${
                msg.isError ? 'onboarding__msg--error' : ''
              }`}
            >
              <div className="onboarding__msg-bubble">
                {msg.sender === 'assistant' && (
                  <div className="onboarding__msg-sender">
                    CALDIM AI Onboarding Assistant
                  </div>
                )}
                <div className="onboarding__msg-text">{msg.text}</div>
              </div>
            </div>
          ))}

          {/* Step 8 Confirmation & Consent Summary */}
          {isConfirmationStep && (
            <div className="onboarding__summary-card-wrapper">
              <Card accent="teal">
                <div className="card__title-group">
                  <h3 className="card__title">Profile Verification & Consent Calibration</h3>
                  <span className="card__subtitle">
                    Review your professional context before beginning the industrial consultation.
                  </span>
                </div>

                {/* Attributes Table with Edit buttons */}
                <div className="onboarding__summary-grid">
                  <div className="onboarding__summary-row">
                    <span className="onboarding__summary-label">Full Name:</span>
                    <strong className="onboarding__summary-value">{visitor.display_name || '—'}</strong>
                    <Button variant="ghost" size="sm" onClick={() => handleEditField(0)}>
                      Edit
                    </Button>
                  </div>

                  <div className="onboarding__summary-row">
                    <span className="onboarding__summary-label">Email Address:</span>
                    <strong className="onboarding__summary-value">{visitor.email || '—'}</strong>
                    <Button variant="ghost" size="sm" onClick={() => handleEditField(1)}>
                      Edit
                    </Button>
                  </div>

                  <div className="onboarding__summary-row">
                    <span className="onboarding__summary-label">Phone Number:</span>
                    <strong className="onboarding__summary-value">{visitor.phone || '—'}</strong>
                    <Button variant="ghost" size="sm" onClick={() => handleEditField(2)}>
                      Edit
                    </Button>
                  </div>

                  <div className="onboarding__summary-row">
                    <span className="onboarding__summary-label">Profession / Role:</span>
                    <strong className="onboarding__summary-value">{visitor.profession || '—'}</strong>
                    <Button variant="ghost" size="sm" onClick={() => handleEditField(3)}>
                      Edit
                    </Button>
                  </div>

                  <div className="onboarding__summary-row">
                    <span className="onboarding__summary-label">Company:</span>
                    <strong className="onboarding__summary-value">{visitor.company_name || '—'}</strong>
                    <Button variant="ghost" size="sm" onClick={() => handleEditField(4)}>
                      Edit
                    </Button>
                  </div>

                  <div className="onboarding__summary-row">
                    <span className="onboarding__summary-label">Industry:</span>
                    <strong className="onboarding__summary-value">{visitor.industry || '—'}</strong>
                    <Button variant="ghost" size="sm" onClick={() => handleEditField(5)}>
                      Edit
                    </Button>
                  </div>

                  <div className="onboarding__summary-row">
                    <span className="onboarding__summary-label">Department / Responsibilities:</span>
                    <strong className="onboarding__summary-value">
                      {visitor.responsibilities || visitor.department || '—'}
                    </strong>
                    <Button variant="ghost" size="sm" onClick={() => handleEditField(6)}>
                      Edit
                    </Button>
                  </div>
                </div>

                {/* Consent Categories Checkboxes */}
                <div className="onboarding__consents-section">
                  <h4 className="onboarding__consents-title">Privacy & Processing Consents</h4>
                  <p className="onboarding__consents-sub">
                    CALDIM enforces transparent, category-specific data rights under GDPR and ISO/IEC 27701 principles.
                  </p>

                  <div className="onboarding__consent-options">
                    {/* 1. Essential Service Processing (Mandatory) */}
                    <label className="onboarding__consent-item onboarding__consent-item--locked">
                      <input
                        type="checkbox"
                        checked={consentEssential}
                        disabled
                        aria-label="Essential Service Processing Consent"
                      />
                      <div className="onboarding__consent-body">
                        <strong>Essential Service Processing (Mandatory)</strong>
                        <span>
                          Required for multi-turn AI reasoning, problem diagnostic extraction, and consultation state persistence.
                        </span>
                      </div>
                    </label>

                    {/* 2. Proposal Communications (Optional) */}
                    <label className="onboarding__consent-item">
                      <input
                        type="checkbox"
                        checked={consentProposals}
                        onChange={(e) => setConsentProposals(e.target.checked)}
                        aria-label="Proposal Communications Consent"
                      />
                      <div className="onboarding__consent-body">
                        <strong>Proposal Communications & Architecture Deliverables (Recommended)</strong>
                        <span>
                          Allows CALDIM solution engineers to send customized PDF architecture blueprints, cost-benefit analyses, and implementation roadmaps to your email or phone.
                        </span>
                      </div>
                    </label>

                    {/* 3. Usage Analytics (Optional) */}
                    <label className="onboarding__consent-item">
                      <input
                        type="checkbox"
                        checked={consentAnalytics}
                        onChange={(e) => setConsentAnalytics(e.target.checked)}
                        aria-label="Usage Analytics Consent"
                      />
                      <div className="onboarding__consent-body">
                        <strong>Usage Analytics & Personalization (Optional)</strong>
                        <span>
                          Permits aggregated, non-sensitive session telemetry to calibrate sector benchmarks and recommendation accuracy.
                        </span>
                      </div>
                    </label>

                    {/* 4. Marketing Updates (Optional) */}
                    <label className="onboarding__consent-item">
                      <input
                        type="checkbox"
                        checked={consentMarketing}
                        onChange={(e) => setConsentMarketing(e.target.checked)}
                        aria-label="Marketing Updates Consent"
                      />
                      <div className="onboarding__consent-body">
                        <strong>Product Announcements & Marketing Updates (Optional)</strong>
                        <span>
                          Receive verified release notes regarding new CALDIM software suites and industrial expo presentations.
                        </span>
                      </div>
                    </label>
                  </div>

                  {consentError && (
                    <div className="onboarding__consent-error">{consentError}</div>
                  )}

                  {pendingChallenge && (
                    <div className="onboarding__pending-banner">
                      <span>Queued Operational Challenge: </span>
                      <strong>&ldquo;{pendingChallenge.slice(0, 90)}...&rdquo;</strong>
                      <span> will automatically run upon confirmation.</span>
                    </div>
                  )}

                  <div className="onboarding__confirm-action">
                    <Button
                      variant="primary"
                      size="lg"
                      onClick={handleConfirmProfileAndConsents}
                      disabled={consentSubmitting || !consentEssential}
                    >
                      {consentSubmitting
                        ? 'Confirming Calibration...'
                        : 'Confirm Profile & Begin Consultation →'}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar (Hidden once at confirmation step) */}
        {!isConfirmationStep && currentStep && (
          <div className="onboarding__input-container">
            <form className="onboarding__input-form" onSubmit={handleStepSubmit}>
              <input
                ref={inputRef}
                type={currentStep.inputType}
                className="onboarding__input"
                placeholder={currentStep.placeholder}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isSubmitting}
                autoFocus
              />
              <Button
                type="submit"
                variant="primary"
                size="md"
                disabled={!inputValue.trim() || isSubmitting}
              >
                {isSubmitting ? 'Saving...' : 'Submit Answer ↵'}
              </Button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
