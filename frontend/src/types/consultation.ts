/**
 * TypeScript types for CALDIM Consultation Engine.
 */

export interface KnowledgeSourceItem {
  chunk_id?: string;
  product_name: string;
  product_slug: string;
  source_url: string;
  section_title?: string;
  trust_level?: string;
}

export interface StructuredAnalysisPayload {
  reply?: string;
  analysis?: {
    root_causes?: string[];
    operational_friction?: string[];
    compliance_or_accuracy_risks?: string[];
  };
  recommendations?: Array<{
    product_name: string;
    product_slug: string;
    suitability_rationale: string;
    source_url: string;
    verified: boolean;
  }>;
  solution_comparison?: {
    primary_solution?: string;
    alternative_approach?: string;
    tradeoff_analysis?: string;
  };
  dynamic_questions?: string[];
  assumptions_and_limitations?: string[];
  next_steps?: string[];
  visual_spec?: {
    diagram_type: string;
    title: string;
    steps: string[];
  };
}

export interface ConsultationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  client_message_id?: string;
  structured_payload?: StructuredAnalysisPayload;
  knowledge_sources?: KnowledgeSourceItem[];
  prompt_tokens?: number;
  completion_tokens?: number;
  latency_ms?: number;
  model_id?: string;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  visitor_id: string;
  title: string;
  challenge_summary: string;
  status: 'active' | 'completed' | 'archived';
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  visitor_id: string;
  title: string;
  challenge_summary: string;
  status: 'active' | 'completed' | 'archived';
  consultation_state: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  messages: ConsultationMessage[];
}

export interface CreateConversationPayload {
  title?: string;
  initial_message: string;
  client_message_id?: string;
}

export interface CreateMessagePayload {
  content: string;
  client_message_id?: string;
}

export interface MessageTurnResponse {
  conversation_id: string;
  consultation_state: Record<string, unknown>;
  assistant_message: ConsultationMessage;
}
