export type ProfileCompletionStatus = 'incomplete' | 'partial' | 'complete';
export type ConsentCategory =
  | 'essential'
  | 'email_contact'
  | 'analytics'
  | 'proposal_delivery'
  | 'marketing';
export type ConsentStatus = 'granted' | 'denied';
export type SessionStatus = 'active' | 'idle' | 'ended' | 'expired';

export interface VisitorProfile {
  id: string;
  display_name: string;
  profession: string;
  company_name: string;
  industry: string;
  department: string;
  responsibilities: string;
  email: string | null;
  phone: string | null;
  profile_completion_status: ProfileCompletionStatus;
  created_at: string;
  updated_at: string;
}

export interface VisitorConsent {
  id: string;
  category: ConsentCategory;
  status: ConsentStatus;
  policy_version: string;
  recorded_at: string;
  revoked_at: string | null;
}

export interface VisitorSession {
  id: string;
  visitor_id: string;
  status: SessionStatus;
  created_at: string;
  last_activity_at: string;
  ended_at: string | null;
  metadata: Record<string, unknown>;
}

export interface CreateVisitorPayload {
  display_name?: string;
  profession?: string;
  company_name?: string;
  industry?: string;
  department?: string;
  responsibilities?: string;
  email?: string;
  phone?: string;
  initial_consents?: Array<{
    category: ConsentCategory;
    status: ConsentStatus;
    policy_version?: string;
  }>;
}

export interface CreateVisitorResponse {
  visitor: VisitorProfile;
  access_token: string;
  message: string;
}

export interface UpdateVisitorPayload {
  display_name?: string;
  profession?: string;
  company_name?: string;
  industry?: string;
  department?: string;
  responsibilities?: string;
  email?: string;
  phone?: string;
}

export interface UpdateVisitorResponse {
  visitor: VisitorProfile;
  consents: VisitorConsent[];
  message: string;
}

