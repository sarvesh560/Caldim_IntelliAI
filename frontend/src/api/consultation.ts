/**
 * Consultation API client for CALDIM IntelliSolve AI.
 * Handles conversation creation, multi-turn messaging, and history retrieval.
 */
import { request } from './client';
import type {
  ConversationDetail,
  ConversationSummary,
  CreateConversationPayload,
  CreateMessagePayload,
  MessageTurnResponse,
} from '../types/consultation';

export const consultationApi = {
  /**
   * Start a new consultation challenge with an initial message.
   */
  async createConversation(
    token: string,
    payload: CreateConversationPayload
  ): Promise<ConversationDetail> {
    const { data } = await request<ConversationDetail>('/api/v1/consultations/', {
      method: 'POST',
      headers: {
        'X-Visitor-Token': token,
      },
      body: JSON.stringify(payload),
    });
    return data;
  },

  /**
   * List all conversations owned by the authenticated visitor.
   */
  async listConversations(
    token: string
  ): Promise<{ count: number; conversations: ConversationSummary[] }> {
    const { data } = await request<{ count: number; conversations: ConversationSummary[] }>(
      '/api/v1/consultations/',
      {
        method: 'GET',
        headers: {
          'X-Visitor-Token': token,
        },
      }
    );
    return data;
  },

  /**
   * Retrieve a full conversation profile and message history.
   */
  async getConversation(
    token: string,
    conversationId: string
  ): Promise<ConversationDetail> {
    const { data } = await request<ConversationDetail>(
      `/api/v1/consultations/${conversationId}/`,
      {
        method: 'GET',
        headers: {
          'X-Visitor-Token': token,
        },
      }
    );
    return data;
  },

  /**
   * Submit a follow-up consultation message turn.
   */
  async sendMessage(
    token: string,
    conversationId: string,
    payload: CreateMessagePayload
  ): Promise<MessageTurnResponse> {
    const { data } = await request<MessageTurnResponse>(
      `/api/v1/consultations/${conversationId}/messages/`,
      {
        method: 'POST',
        headers: {
          'X-Visitor-Token': token,
        },
        body: JSON.stringify(payload),
      }
    );
    return data;
  },
};
