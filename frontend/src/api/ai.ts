import { fetchApi, postApi } from './client';
import {
  AIAnalysisResponse,
  AIReviewQueueResponse,
  AIFeedbackCreate,
  AIFeedbackResponse,
} from '@/types/api';

export interface ListAIAnalysesParams {
  analysis_type?: string;
  status?: string;
  offset?: number;
  limit?: number;
}

export const aiApi = {
  listAnalyses: (params?: ListAIAnalysesParams) =>
    fetchApi<AIAnalysisResponse[]>('/ai/analyses', { params }),

  getAnalysis: (analysisId: string) =>
    fetchApi<AIAnalysisResponse>(`/ai/analyses/${analysisId}`),

  getReviewQueue: (page = 1, pageSize = 20, includeReviewed = false) =>
    fetchApi<AIReviewQueueResponse>('/ai/review-queue', {
      params: { page, page_size: pageSize, include_reviewed: includeReviewed },
    }),

  submitFeedback: (analysisId: string, data: AIFeedbackCreate) =>
    postApi<AIFeedbackResponse>(`/ai/analyses/${analysisId}/feedback`, data),

  analyzeLead: (
    leadId: string,
    content: string,
    customerContext = '',
    productContext = '',
    conversationContext = '',
    forceRefresh = false
  ) =>
    postApi<any>(`/ai/leads/${leadId}/analyze`, null, {
      params: {
        content,
        customer_context: customerContext,
        product_context: productContext,
        conversation_context: conversationContext,
        force_refresh: forceRefresh,
      },
    }),

  analyzeConversation: (conversationId: string, forceRefresh = false) =>
    postApi<any>(`/ai/conversations/${conversationId}/analyze`, null, {
      params: { force_refresh: forceRefresh },
    }),

  recommendLeadFollowup: (
    leadId: string,
    leadContext: string,
    conversationContext: string,
    autoSchedule = true,
    forceRefresh = false
  ) =>
    postApi<any>(`/ai/leads/${leadId}/followup`, null, {
      params: {
        lead_context: leadContext,
        conversation_context: conversationContext,
        auto_schedule: autoSchedule,
        force_refresh: forceRefresh,
      },
    }),
};
