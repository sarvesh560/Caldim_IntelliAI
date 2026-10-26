import { request } from './client';
import type {
  CreateVisitorPayload,
  CreateVisitorResponse,
  VisitorProfile,
  VisitorConsent,
  VisitorSession,
  ConsentCategory,
  ConsentStatus,
} from '../types/visitor';

/**
 * Visitor API service
 * Manages visitor profiles, explicit consents, and consultation sessions.
 */
export const visitorApi = {
  /**
   * Create a new visitor profile with optional initial consent records.
   */
  async createVisitor(payload: CreateVisitorPayload): Promise<CreateVisitorResponse> {
    const { data } = await request<CreateVisitorResponse>('/api/v1/visitors/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return data;
  },

  /**
   * Retrieve visitor profile and active consents using ownership token.
   */
  async getVisitorProfile(
    visitorId: string,
    token: string
  ): Promise<{ visitor: VisitorProfile; consents: VisitorConsent[] }> {
    const { data } = await request<{ visitor: VisitorProfile; consents: VisitorConsent[] }>(
      `/api/v1/visitors/${visitorId}/`,
      {
        method: 'GET',
        headers: {
          'X-Visitor-Token': token,
          'Authorization': `Bearer ${token}`,
        },
      }
    );
    return data;
  },

  /**
   * Incrementally update visitor profile context during conversational onboarding.
   */
  async updateVisitorProfile(
    visitorId: string,
    token: string,
    payload: {
      display_name?: string;
      profession?: string;
      company_name?: string;
      industry?: string;
      department?: string;
      responsibilities?: string;
      email?: string;
      phone?: string;
    }
  ): Promise<{ visitor: VisitorProfile; consents: VisitorConsent[]; message: string }> {
    const { data } = await request<{
      visitor: VisitorProfile;
      consents: VisitorConsent[];
      message: string;
    }>(`/api/v1/visitors/${visitorId}/`, {
      method: 'PATCH',
      headers: {
        'X-Visitor-Token': token,
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return data;
  },

  /**
   * Establish a new consultation session for an authorized visitor.
   */
  async createSession(
    visitorId: string,
    token: string,
    metadata: Record<string, unknown> = {}
  ): Promise<VisitorSession> {
    const { data } = await request<VisitorSession>(
      `/api/v1/visitors/${visitorId}/sessions/`,
      {
        method: 'POST',
        headers: {
          'X-Visitor-Token': token,
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ metadata }),
      }
    );
    return data;
  },

  /**
   * Record or update an explicit consent status for an authorized visitor.
   */
  async recordConsent(
    visitorId: string,
    token: string,
    category: ConsentCategory,
    status: ConsentStatus,
    policyVersion = '1.0'
  ): Promise<VisitorConsent> {
    const { data } = await request<VisitorConsent>(
      `/api/v1/visitors/${visitorId}/consent/`,
      {
        method: 'POST',
        headers: {
          'X-Visitor-Token': token,
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          category,
          status,
          policy_version: policyVersion,
        }),
      }
    );
    return data;
  },
};

