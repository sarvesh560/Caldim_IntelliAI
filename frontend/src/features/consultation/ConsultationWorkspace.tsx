import React, { useState, useEffect, useRef, useMemo } from 'react';
import { consultationApi } from '../../api/consultation';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import type { VisitorProfile } from '../../types/visitor';
import type {
  ConversationDetail,
  StructuredAnalysisPayload,
  KnowledgeSourceItem,
} from '../../types/consultation';
import './ConsultationWorkspace.css';

interface ConsultationWorkspaceProps {
  token: string;
  visitor: VisitorProfile | null;
  initialChallenge?: string;
  onBackToShowroom: () => void;
  onUpdateProfile?: (data: {
    displayName?: string;
    email?: string;
    phone?: string;
    profession?: string;
    companyName?: string;
    industry?: string;
    department?: string;
    responsibilities?: string;
    display_name?: string;
    company_name?: string;
  }) => Promise<VisitorProfile | undefined>;
}

export interface UnifiedChatMessage {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  isError?: boolean;
  timestamp?: string;
  knowledge_sources?: KnowledgeSourceItem[];
  structured_payload?: StructuredAnalysisPayload;
  isCalibrationNotice?: boolean;
}

interface QuestionConfig {
  step: number;
  label: string;
  field: 'displayName' | 'email' | 'profession' | 'companyName' | 'industry' | 'department';
  getPrompt: (firstName?: string) => string;
  placeholder: string;
  validate: (val: string) => string | null;
}

export const ONBOARDING_QUESTIONS: QuestionConfig[] = [
  {
    step: 0,
    label: 'Full Name',
    field: 'displayName',
    getPrompt: () => 'Hello! Welcome to CALDIM IntelliSolve AI. Before we begin, what is your full name?',
    placeholder: 'e.g. Elena Vance or Marcus Thorne',
    validate: (val: string) => {
      const clean = val.trim();
      if (clean.length < 2) return "Please enter your full name (at least 2 characters) so I know who I'm speaking with.";
      return null;
    },
  },
  {
    step: 1,
    label: 'Email Address',
    field: 'email',
    getPrompt: (firstName) => `Nice to meet you, ${firstName || 'there'}! What is your email address?`,
    placeholder: 'e.g. name@organization.com',
    validate: (val: string) => {
      const clean = val.trim();
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(clean)) {
        return "That doesn't look like a valid email address. Please enter a valid email format (e.g. name@organization.com).";
      }
      return null;
    },
  },
  {
    step: 2,
    label: 'Profession / Job Title',
    field: 'profession',
    getPrompt: () => 'Thank you! What is your profession or current job title?',
    placeholder: 'e.g. Production Manager, Maintenance Engineer, Software Engineer, Business Owner',
    validate: (val: string) => {
      if (val.trim().length < 2) return 'Please specify your profession or job title (at least 2 characters).';
      return null;
    },
  },
  {
    step: 3,
    label: 'Company',
    field: 'companyName',
    getPrompt: () => 'Which company or organization do you work with?',
    placeholder: "e.g. Apex Precision Mfg, or 'Self-employed', 'Student', 'I\\'d prefer not to say'",
    validate: (val: string) => {
      if (val.trim().length < 2) return "Please provide your organization name, or you may say 'Self-employed', 'Student', or 'I\\'d prefer not to say'.";
      return null;
    },
  },
  {
    step: 4,
    label: 'Industry',
    field: 'industry',
    getPrompt: () => 'What industry or type of business are you involved in?',
    placeholder: 'e.g. Textile manufacturing, Automotive, Healthcare, Education, Retail, IT, Logistics',
    validate: (val: string) => {
      if (val.trim().length < 2) return 'Please specify your industry or type of business (at least 2 characters).';
      return null;
    },
  },
  {
    step: 5,
    label: 'Department and Responsibilities',
    field: 'department',
    getPrompt: () => 'Which department do you work in, and what are your main responsibilities?',
    placeholder: 'e.g. Operations Engineering, managing line availability and shift OEE targets',
    validate: (val: string) => {
      if (val.trim().length < 2) return 'Please share your department and key responsibilities so I can tailor our consultation.';
      return null;
    },
  },
];

export function resolveProfessionCategory(profession?: string): { category: string; label: string } {
  const clean = (profession || '').toLowerCase().trim();
  if (!clean) return { category: 'general_professional', label: 'Industrial Professional' };

  if (/\b(production|manufacturing|plant\s*manager|factory|shopfloor|shift\s*supervisor|assembly|line\s*manager|mill\s*manager|works\s*manager|fabrication\s*manager|operations\s*manager)\b/i.test(clean)) {
    return { category: 'production_manufacturing', label: 'Production & Manufacturing' };
  }
  if (/\b(maintenance|reliability|equipment|technician|tooling|preventive|pm\s*engineer|electrical\s*engineer|mechanical\s*engineer|instrumentation|millwright|breakdown)\b/i.test(clean)) {
    return { category: 'maintenance_reliability', label: 'Maintenance & Reliability' };
  }
  if (/\b(quality|qa|qc|inspection|compliance|six\s*sigma|iso|metrology|calibration|testing|audit|qms)\b/i.test(clean)) {
    return { category: 'quality_assurance', label: 'Quality Assurance & QC' };
  }
  if (/\b(industrial\s*engineer|process\s*engineer|continuous\s*improvement|kaizen|lean|value\s*stream|method\s*engineer|operational\s*excellence|op-ex)\b/i.test(clean)) {
    return { category: 'industrial_process', label: 'Industrial Process & Lean' };
  }
  if (/\b(software|developer|programmer|devops|architect|cto|tech\s*lead|systems\s*admin|cloud|database|it\s*manager|data\s*engineer|fullstack|backend|frontend)\b/i.test(clean)) {
    return { category: 'software_it', label: 'Software & IT Architecture' };
  }
  if (/\b(supply\s*chain|logistics|warehouse|procurement|purchasing|inventory|dispatcher|fleet|freight|stores\s*manager|materials\s*manager)\b/i.test(clean)) {
    return { category: 'supply_chain_logistics', label: 'Supply Chain & Logistics' };
  }
  if (/\b(finance|financial|cfo|controller|accountant|auditor|billing|bookkeeper|treasurer|costing|budget)\b/i.test(clean)) {
    return { category: 'finance_accounting', label: 'Finance & Accounting' };
  }
  if (/\b(hr|human\s*resources|talent|recruiter|recruitment|payroll|people\s*ops|workforce|training|timekeeping)\b/i.test(clean)) {
    return { category: 'hr_workforce', label: 'HR & Workforce Management' };
  }
  if (/\b(sales|marketing|commercial|business\s*development|bd|account\s*executive|customer\s*success|client\s*relations|revenue)\b/i.test(clean)) {
    return { category: 'sales_marketing', label: 'Sales & Marketing' };
  }
  if (/\b(owner|founder|ceo|managing\s*director|md|general\s*manager|gm|president|partner|executive|director|co-founder|proprietor)\b/i.test(clean)) {
    return { category: 'business_leadership', label: 'Executive & Business Leadership' };
  }
  if (/\b(consultant|advisor|analyst|researcher|scientist|professor|student|intern|scholar|fellow)\b/i.test(clean)) {
    return { category: 'consultant_researcher', label: 'Consulting & Research' };
  }
  return { category: 'general_professional', label: 'Industrial Professional' };
}

function getMissingStepIndex(v: VisitorProfile | null): number {
  if (!v) return 0;
  if (!v.display_name?.trim()) return 0;
  if (!v.email?.trim()) return 1;
  if (!v.profession?.trim()) return 2;
  if (!v.company_name?.trim()) return 3;
  if (!v.industry?.trim()) return 4;
  if (!v.department?.trim() && !v.responsibilities?.trim()) return 5;
  return 6; // All 6 completed
}

export const ConsultationWorkspace: React.FC<ConsultationWorkspaceProps> = ({
  token,
  visitor,
  initialChallenge,
  onBackToShowroom,
  onUpdateProfile,
}) => {
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [unifiedMessages, setUnifiedMessages] = useState<UnifiedChatMessage[]>([]);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [inputContent, setInputContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCalibratingProfile, setIsCalibratingProfile] = useState(false);

  // Calibration Form State
  const [calibName, setCalibName] = useState('');
  const [calibEmail, setCalibEmail] = useState('');
  const [calibProfession, setCalibProfession] = useState('');
  const [calibCompany, setCalibCompany] = useState('');
  const [calibIndustry, setCalibIndustry] = useState('');
  const [calibDept, setCalibDept] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitializedRef = useRef(false);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [unifiedMessages, isLoading]);

  // Derived role category
  const roleCategory = useMemo(() => resolveProfessionCategory(visitor?.profession), [visitor?.profession]);

  // Count calibrated fields
  const calibratedCount = useMemo(() => {
    if (!visitor) return 0;
    let count = 0;
    if (visitor.display_name?.trim()) count++;
    if (visitor.email?.trim()) count++;
    if (visitor.profession?.trim()) count++;
    if (visitor.company_name?.trim()) count++;
    if (visitor.industry?.trim()) count++;
    if (visitor.department?.trim() || visitor.responsibilities?.trim()) count++;
    return count;
  }, [visitor]);

  // Sync calibration form fields when visitor updates or modal opens
  useEffect(() => {
    if (visitor) {
      setCalibName(visitor.display_name || '');
      setCalibEmail(visitor.email || '');
      setCalibProfession(visitor.profession || '');
      setCalibCompany(visitor.company_name || '');
      setCalibIndustry(visitor.industry || '');
      setCalibDept(visitor.department || visitor.responsibilities || '');
    }
  }, [visitor, isCalibratingProfile]);

  // Initialize unified chat history from visitor profile and server state
  useEffect(() => {
    if (hasInitializedRef.current) return;
    if (!visitor) return;

    hasInitializedRef.current = true;
    const step = getMissingStepIndex(visitor);
    setCurrentStep(step);

    const msgs: UnifiedChatMessage[] = [];
    const firstName = visitor.display_name?.trim() ? visitor.display_name.trim().split(' ')[0] : '';

    // Step 0: Name
    msgs.push({
      id: 'onb-q-0',
      role: 'assistant',
      content: ONBOARDING_QUESTIONS[0].getPrompt(),
    });
    if (visitor.display_name?.trim()) {
      msgs.push({ id: 'onb-a-0', role: 'user', content: visitor.display_name });
    } else {
      setUnifiedMessages(msgs);
      return;
    }

    // Step 1: Email
    msgs.push({
      id: 'onb-q-1',
      role: 'assistant',
      content: ONBOARDING_QUESTIONS[1].getPrompt(firstName),
    });
    if (visitor.email?.trim()) {
      msgs.push({ id: 'onb-a-1', role: 'user', content: visitor.email });
    } else {
      setUnifiedMessages(msgs);
      return;
    }

    // Step 2: Profession
    msgs.push({
      id: 'onb-q-2',
      role: 'assistant',
      content: ONBOARDING_QUESTIONS[2].getPrompt(),
    });
    if (visitor.profession?.trim()) {
      msgs.push({ id: 'onb-a-2', role: 'user', content: visitor.profession });
    } else {
      setUnifiedMessages(msgs);
      return;
    }

    // Step 3: Company
    msgs.push({
      id: 'onb-q-3',
      role: 'assistant',
      content: ONBOARDING_QUESTIONS[3].getPrompt(),
    });
    if (visitor.company_name?.trim()) {
      msgs.push({ id: 'onb-a-3', role: 'user', content: visitor.company_name });
    } else {
      setUnifiedMessages(msgs);
      return;
    }

    // Step 4: Industry
    msgs.push({
      id: 'onb-q-4',
      role: 'assistant',
      content: ONBOARDING_QUESTIONS[4].getPrompt(),
    });
    if (visitor.industry?.trim()) {
      msgs.push({ id: 'onb-a-4', role: 'user', content: visitor.industry });
    } else {
      setUnifiedMessages(msgs);
      return;
    }

    // Step 5: Department & Responsibilities
    msgs.push({
      id: 'onb-q-5',
      role: 'assistant',
      content: ONBOARDING_QUESTIONS[5].getPrompt(),
    });
    const deptResp = visitor.responsibilities?.trim() || visitor.department?.trim();
    if (deptResp) {
      msgs.push({ id: 'onb-a-5', role: 'user', content: deptResp });
    } else {
      setUnifiedMessages(msgs);
      return;
    }

    // All 6 complete: Transition into Consultation
    msgs.push({
      id: 'onb-transition',
      role: 'assistant',
      content: `Thanks, ${firstName || 'there'}. I'll tailor our discussion to your work as a ${visitor.profession} in ${visitor.industry}. What challenge would you like to solve today?`,
    });

    setUnifiedMessages(msgs);

    // If an initial challenge was provided and profile is complete, auto-start first consultation turn
    if (initialChallenge && step >= 6) {
      triggerConsultationTurn(initialChallenge);
    }
  }, [visitor]);

  // Trigger consultation turn via API
  const triggerConsultationTurn = async (userPrompt: string) => {
    if (!token || isLoading) return;
    setIsLoading(true);
    setError(null);

    const clientMsgId = `msg-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const optimisticMsg: UnifiedChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userPrompt,
      timestamp: new Date().toISOString(),
    };

    setUnifiedMessages((prev) => [...prev, optimisticMsg]);

    try {
      if (!conversation) {
        // Start brand new consultation conversation
        const conv = await consultationApi.createConversation(token, {
          initial_message: userPrompt,
          client_message_id: clientMsgId,
        });
        setConversation(conv);

        // Fetch latest assistant turn from response
        const assistantTurn = conv.messages.slice().reverse().find((m) => m.role === 'assistant');
        if (assistantTurn) {
          setUnifiedMessages((prev) => [
            ...prev,
            {
              id: assistantTurn.id,
              role: 'assistant',
              content: assistantTurn.content,
              structured_payload: assistantTurn.structured_payload,
              knowledge_sources: assistantTurn.knowledge_sources,
              timestamp: assistantTurn.created_at,
            },
          ]);
        }
      } else {
        // Submit follow-up message to active conversation
        const response = await consultationApi.sendMessage(token, conversation.id, {
          content: userPrompt,
          client_message_id: clientMsgId,
        });

        setConversation((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            consultation_state: response.consultation_state,
            messages: [...prev.messages, response.assistant_message],
          };
        });

        setUnifiedMessages((prev) => [
          ...prev,
          {
            id: response.assistant_message.id,
            role: 'assistant',
            content: response.assistant_message.content,
            structured_payload: response.assistant_message.structured_payload,
            knowledge_sources: response.assistant_message.knowledge_sources,
            timestamp: response.assistant_message.created_at,
          },
        ]);
      }
    } catch (err: unknown) {
      console.error('Consultation turn failed:', err);
      setError('Unable to receive consultation turn from the AI service. Please verify backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // Shared Message Submission Handler (Supports both Onboarding Questions and Consultation Turns)
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = inputContent.trim();
    if (!clean || isLoading) return;

    setInputContent('');
    setError(null);

    // ==========================================
    // PHASE A: MANDATORY ONBOARDING PROFILE FLOW
    // ==========================================
    if (currentStep < 6) {
      const qConfig = ONBOARDING_QUESTIONS[currentStep];
      const validationError = qConfig.validate(clean);

      if (validationError) {
        // Preserve prior valid answers; post friendly error message in-chat
        setUnifiedMessages((prev) => [
          ...prev,
          {
            id: `usr-err-${Date.now()}`,
            role: 'user',
            content: clean,
          },
          {
            id: `ast-err-${Date.now()}`,
            role: 'assistant',
            content: validationError,
            isError: true,
          },
        ]);
        return;
      }

      // Valid Answer: Add user turn
      setUnifiedMessages((prev) => [
        ...prev,
        {
          id: `usr-step-${currentStep}-${Date.now()}`,
          role: 'user',
          content: clean,
        },
      ]);

      setIsLoading(true);
      try {
        let updatedVisitor: VisitorProfile | undefined;
        if (onUpdateProfile) {
          if (currentStep === 0) {
            updatedVisitor = await onUpdateProfile({ displayName: clean });
          } else if (currentStep === 1) {
            updatedVisitor = await onUpdateProfile({ email: clean });
          } else if (currentStep === 2) {
            updatedVisitor = await onUpdateProfile({ profession: clean });
          } else if (currentStep === 3) {
            updatedVisitor = await onUpdateProfile({ companyName: clean });
          } else if (currentStep === 4) {
            updatedVisitor = await onUpdateProfile({ industry: clean });
          } else if (currentStep === 5) {
            updatedVisitor = await onUpdateProfile({
              department: clean,
              responsibilities: clean,
            });
          }
        }

        const nextStep = currentStep + 1;
        setCurrentStep(nextStep);

        const currentName = updatedVisitor?.display_name || visitor?.display_name || '';
        const firstName = currentName.trim().split(' ')[0] || 'there';

        if (nextStep < 6) {
          // Advance to next question in sequence
          const nextQ = ONBOARDING_QUESTIONS[nextStep];
          setUnifiedMessages((prev) => [
            ...prev,
            {
              id: `ast-step-${nextStep}-${Date.now()}`,
              role: 'assistant',
              content: nextQ.getPrompt(firstName),
            },
          ]);
        } else {
          // All 6 required fields completed! Transition to AI Consultation
          const finalProfession = updatedVisitor?.profession || visitor?.profession || 'Industrial Leader';
          const finalIndustry = updatedVisitor?.industry || visitor?.industry || 'Manufacturing';

          const transitionMsg = `Thanks, ${firstName}. I'll tailor our discussion to your work as a ${finalProfession} in ${finalIndustry}. What challenge would you like to solve today?`;

          setUnifiedMessages((prev) => [
            ...prev,
            {
              id: `ast-complete-${Date.now()}`,
              role: 'assistant',
              content: transitionMsg,
            },
          ]);

          // If visitor clicked a showroom challenge before completing onboarding, start it now!
          if (initialChallenge) {
            setTimeout(() => {
              triggerConsultationTurn(initialChallenge);
            }, 600);
          }
        }
      } catch (patchErr: unknown) {
        console.error('Failed to progressively update visitor profile:', patchErr);
        setError('Encountered an issue saving your profile answer. Please retry.');
      } finally {
        setIsLoading(false);
      }
      return;
    }

    // ==========================================
    // PHASE B: ACTIVE AI CONSULTATION TURNS
    // ==========================================
    await triggerConsultationTurn(clean);
  };

  // Profile Calibration Save Handler
  const handleSaveCalibration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onUpdateProfile) return;

    setIsLoading(true);
    try {
      await onUpdateProfile({
        displayName: calibName.trim(),
        email: calibEmail.trim(),
        profession: calibProfession.trim(),
        companyName: calibCompany.trim(),
        industry: calibIndustry.trim(),
        department: calibDept.trim(),
        responsibilities: calibDept.trim(),
      });

      setIsCalibratingProfile(false);
      const newCategory = resolveProfessionCategory(calibProfession);

      // Post notification in unified timeline
      setUnifiedMessages((prev) => [
        ...prev,
        {
          id: `calib-notice-${Date.now()}`,
          role: 'assistant',
          content: `⚙️ Profile Calibrated: Your role is now set to ${calibProfession || 'Industrial Leader'} (${newCategory.label}) at ${calibCompany || 'Enterprise'}. Upcoming AI consultation turns will dynamically tailor their technical directives to this context.`,
          isCalibrationNotice: true,
        },
      ]);
    } catch (err: unknown) {
      console.error('Failed to calibrate profile:', err);
      setError('Failed to update profile calibration. Please verify input fields.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectQuestion = (q: string) => {
    setInputContent(q);
  };

  // Find latest assistant structured payload
  const latestAssistantMsg = unifiedMessages
    .slice()
    .reverse()
    .find((m) => m.role === 'assistant' && m.structured_payload);
  const payload: StructuredAnalysisPayload | undefined = latestAssistantMsg?.structured_payload;

  // Placeholder based on current state
  const inputPlaceholder = useMemo(() => {
    if (currentStep < 6) {
      return ONBOARDING_QUESTIONS[currentStep].placeholder;
    }
    return 'State your operational constraints, software environment, or respond to dynamic questions...';
  }, [currentStep]);

  return (
    <div className="consultation-workspace">
      {/* Left Chat Stream */}
      <div className="consultation__chat-col">
        <div className="consultation__chat-header">
          <div className="consultation__chat-title-group">
            <h2 className="consultation__chat-title">
              {conversation?.title || 'Industrial AI Consultation Workspace'}
            </h2>
            <div className="consultation__chat-visitor">
              Consulting for{' '}
              <strong>{visitor?.display_name || visitor?.profession || 'Industrial Leader'}</strong>
              {visitor?.company_name ? ` @ ${visitor.company_name}` : ''}
              {visitor?.industry ? ` (${visitor.industry})` : ''}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCalibratingProfile((prev) => !prev)}
            >
              ⚙ Profile Calibration
            </Button>
            <Badge variant="cyan" size="sm">
              Live Session
            </Badge>
            <Button variant="ghost" size="sm" onClick={onBackToShowroom}>
              ← Showroom
            </Button>
          </div>
        </div>

        {/* Message Thread */}
        <div className="consultation__messages-list">
          {unifiedMessages.map((msg) => (
            <div
              key={msg.id}
              className={`consultation__msg consultation__msg--${msg.role} ${
                msg.isError ? 'consultation__msg--error' : ''
              } ${msg.isCalibrationNotice ? 'consultation__msg--calibration' : ''}`}
            >
              <div className="consultation__msg-bubble">
                <div className="consultation__msg-reply">
                  {msg.role === 'assistant'
                    ? msg.structured_payload?.reply || msg.content
                    : msg.content}
                </div>

                {/* Source Provenance */}
                {msg.role === 'assistant' && msg.knowledge_sources && msg.knowledge_sources.length > 0 && (
                  <div className="consultation__msg-sources">
                    {msg.knowledge_sources.map((s, idx) => (
                      <a
                        key={idx}
                        href={s.source_url || '#'}
                        target="_blank"
                        rel="noreferrer"
                        className="consultation__source-pill"
                      >
                        📄 {s.product_name}
                        {s.section_title ? ` • ${s.section_title}` : ''}
                      </a>
                    ))}
                  </div>
                )}

                {/* Dynamic Questions Chips */}
                {msg.role === 'assistant' &&
                  msg.structured_payload?.dynamic_questions &&
                  msg.structured_payload.dynamic_questions.length > 0 && (
                    <div className="consultation__dynamic-questions">
                      <div className="consultation__dynamic-questions-title">
                        Clarifying Questions (Click to Answer):
                      </div>
                      {msg.structured_payload.dynamic_questions.map((q, idx) => (
                        <div
                          key={idx}
                          className="consultation__question-chip"
                          onClick={() => handleSelectQuestion(q)}
                          role="button"
                          tabIndex={0}
                        >
                          <span>{q}</span>
                          <span style={{ color: 'var(--color-primary-teal)', fontWeight: 'bold' }}>+</span>
                        </div>
                      ))}
                    </div>
                  )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="consultation__msg consultation__msg--assistant">
              <div
                className="consultation__msg-bubble"
                style={{
                  background: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  boxShadow: 'var(--shadow-subtle)',
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    background: 'var(--color-primary-teal)',
                    animation: 'ping 1s infinite',
                  }}
                ></span>
                <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
                  {currentStep < 6
                    ? 'Updating calibrated visitor context...'
                    : 'Analyzing operational challenge & evaluating verified CALDIM architecture...'}
                </span>
              </div>
            </div>
          )}

          {error && (
            <div
              style={{
                padding: '12px 16px',
                background: '#FEE2E2',
                border: '1px solid #FECACA',
                borderRadius: '8px',
                color: '#DC2626',
                fontSize: '0.85rem',
              }}
            >
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Unified Input Bar (Shared Across Onboarding and Consultation) */}
        <div className="consultation__input-container">
          <form className="consultation__input-form" onSubmit={handleSendMessage}>
            <textarea
              className="consultation__textarea"
              placeholder={inputPlaceholder}
              value={inputContent}
              onChange={(e) => setInputContent(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              rows={2}
            />
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!inputContent.trim() || isLoading}
            >
              {currentStep < 6 ? 'Next Step →' : 'Send Turn →'}
            </Button>
          </form>
        </div>
      </div>

      {/* Right Architecture & Intelligence Column */}
      <div className="consultation__findings-col">
        {/* Profile Calibration & Sector Telemetry Card */}
        <Card accent="teal">
          <div className="card__title-group">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <h3 className="card__title">Visitor Profile Calibration</h3>
              <Badge variant={currentStep >= 6 ? 'emerald' : 'cyan'} size="sm">
                {currentStep >= 6 ? 'Calibrated 100%' : `${calibratedCount}/6 Required Fields`}
              </Badge>
            </div>
            <span className="card__subtitle">Cognitive tailoring telemetry for real LLM reasoning</span>
          </div>

          <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="consultation__calibration-field">
              <span className="consultation__calibration-label">Full Name:</span>
              <span className="consultation__calibration-value">
                {visitor?.display_name || <em style={{ color: 'var(--color-text-muted)' }}>Awaiting input...</em>}
              </span>
            </div>

            <div className="consultation__calibration-field">
              <span className="consultation__calibration-label">Email:</span>
              <span className="consultation__calibration-value">
                {visitor?.email || <em style={{ color: 'var(--color-text-muted)' }}>Awaiting input...</em>}
              </span>
            </div>

            <div className="consultation__calibration-field">
              <span className="consultation__calibration-label">Profession:</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="consultation__calibration-value">
                  {visitor?.profession || <em style={{ color: 'var(--color-text-muted)' }}>Awaiting input...</em>}
                </span>
                {visitor?.profession && (
                  <Badge variant="cyan" size="sm">
                    {roleCategory.label}
                  </Badge>
                )}
              </div>
            </div>

            <div className="consultation__calibration-field">
              <span className="consultation__calibration-label">Company:</span>
              <span className="consultation__calibration-value">
                {visitor?.company_name || <em style={{ color: 'var(--color-text-muted)' }}>Awaiting input...</em>}
              </span>
            </div>

            <div className="consultation__calibration-field">
              <span className="consultation__calibration-label">Industry:</span>
              <span className="consultation__calibration-value">
                {visitor?.industry || <em style={{ color: 'var(--color-text-muted)' }}>Awaiting input...</em>}
              </span>
            </div>

            <div className="consultation__calibration-field">
              <span className="consultation__calibration-label">Dept & Scope:</span>
              <span className="consultation__calibration-value">
                {visitor?.department || visitor?.responsibilities || (
                  <em style={{ color: 'var(--color-text-muted)' }}>Awaiting input...</em>
                )}
              </span>
            </div>

            <div
              style={{
                marginTop: '10px',
                paddingTop: '8px',
                borderTop: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                🔒 Essential Processing: <strong>Granted</strong>
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsCalibratingProfile((prev) => !prev)}
              >
                {isCalibratingProfile ? 'Cancel' : 'Edit Calibration'}
              </Button>
            </div>
          </div>

          {/* Inline Calibration Editor */}
          {isCalibratingProfile && (
            <form onSubmit={handleSaveCalibration} className="consultation__calibration-form">
              <div className="consultation__calib-grid">
                <div>
                  <label>Full Name</label>
                  <input
                    type="text"
                    value={calibName}
                    onChange={(e) => setCalibName(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label>Email Address</label>
                  <input
                    type="email"
                    value={calibEmail}
                    onChange={(e) => setCalibEmail(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label>Profession / Job Title</label>
                  <input
                    type="text"
                    value={calibProfession}
                    onChange={(e) => setCalibProfession(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label>Company / Organization</label>
                  <input
                    type="text"
                    value={calibCompany}
                    onChange={(e) => setCalibCompany(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label>Industry</label>
                  <input
                    type="text"
                    value={calibIndustry}
                    onChange={(e) => setCalibIndustry(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label>Department & Scope</label>
                  <input
                    type="text"
                    value={calibDept}
                    onChange={(e) => setCalibDept(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsCalibratingProfile(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" disabled={isLoading}>
                  Save Calibration →
                </Button>
              </div>
            </form>
          )}
        </Card>

        {/* Operational Root Causes */}
        <Card accent="teal">
          <div className="card__title-group">
            <h3 className="card__title">Operational Root Causes</h3>
            <span className="card__subtitle">Diagnostic breakdown from multi-turn consultation</span>
          </div>

          <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {payload?.analysis?.root_causes && payload.analysis.root_causes.length > 0 ? (
              payload.analysis.root_causes.map((rc, idx) => (
                <div key={idx} className="consultation__finding-item">
                  <span className="consultation__finding-bullet">•</span>
                  <span>{rc}</span>
                </div>
              ))
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                {currentStep < 6
                  ? 'Complete your profile in the chat to begin diagnostic analysis.'
                  : 'State your operational challenge to extract technical root causes.'}
              </p>
            )}

            {payload?.analysis?.operational_friction && payload.analysis.operational_friction.length > 0 && (
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-color)' }}>
                <strong style={{ fontSize: '0.75rem', color: 'var(--color-primary-teal)', textTransform: 'uppercase' }}>
                  Friction & Bottlenecks:
                </strong>
                {payload.analysis.operational_friction.map((f, idx) => (
                  <div key={idx} className="consultation__finding-item" style={{ marginTop: '4px' }}>
                    <span className="consultation__finding-bullet">-</span>
                    <span>{f}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Solution Architecture Comparison */}
        <Card accent="purple">
          <div className="card__title-group">
            <h3 className="card__title">Solution Architecture Comparison</h3>
            <span className="card__subtitle">Evaluated alternatives & trade-off analysis</span>
          </div>

          {payload?.solution_comparison ? (
            <div style={{ marginTop: '14px' }}>
              <div className="consultation__comparison-grid">
                <div className="consultation__comparison-box consultation__comparison-box--primary">
                  <h4>Recommended Architecture</h4>
                  <div>{payload.solution_comparison.primary_solution || 'Direct Module Automation'}</div>
                </div>
                <div className="consultation__comparison-box consultation__comparison-box--alt">
                  <h4>Alternative / Status Quo</h4>
                  <div>{payload.solution_comparison.alternative_approach || 'Manual Reconciliation'}</div>
                </div>
              </div>

              {payload.solution_comparison.tradeoff_analysis && (
                <div className="consultation__tradeoff">
                  <strong>Trade-Off Evaluation: </strong>
                  {payload.solution_comparison.tradeoff_analysis}
                </div>
              )}
            </div>
          ) : (
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '12px' }}>
              Architectural trade-offs will populate as problem parameters are clarified.
            </p>
          )}
        </Card>

        {/* Verified Product Recommendations */}
        <Card accent="emerald">
          <div className="card__title-group">
            <h3 className="card__title">Grounded CALDIM Recommendations</h3>
            <span className="card__subtitle">Source-verified module alignment</span>
          </div>

          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {payload?.recommendations && payload.recommendations.length > 0 ? (
              payload.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 14px',
                    background: 'var(--color-surface-subtle)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--color-text-main)' }}>
                      {rec.product_name}
                    </strong>
                    <Badge variant={rec.verified ? 'emerald' : 'amber'} size="sm">
                      {rec.verified ? 'Verified Published' : 'Preview / Custom'}
                    </Badge>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: '6px' }}>
                    {rec.suitability_rationale}
                  </p>
                  {rec.source_url && (
                    <a
                      href={rec.source_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontSize: '0.75rem', marginTop: '6px', display: 'inline-block', fontWeight: 600 }}
                    >
                      Official Source Documentation ↗
                    </a>
                  )}
                </div>
              ))
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                No active module recommended yet.
              </p>
            )}
          </div>
        </Card>

        {/* Implementation Roadmap */}
        <Card>
          <div className="card__title-group">
            <h3 className="card__title">Implementation Roadmap</h3>
            <span className="card__subtitle">Phased deployment milestones</span>
          </div>

          <div className="consultation__roadmap-list" style={{ marginTop: '14px' }}>
            {payload?.next_steps && payload.next_steps.length > 0 ? (
              payload.next_steps.map((step, idx) => (
                <div key={idx} className="consultation__roadmap-step">
                  <div className="consultation__step-num">{idx + 1}</div>
                  <div>{step}</div>
                </div>
              ))
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                Deployment roadmap phases will be generated based on your operational timeline.
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
