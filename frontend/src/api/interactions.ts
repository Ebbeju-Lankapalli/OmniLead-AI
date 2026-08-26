import { fetchApi, postApi, patchApi } from './client';
import { InteractionResponse, InteractionCreateRequest } from '@/types/api';

export interface ListInteractionsParams {
  customer_id?: string;
  lead_id?: string;
  conversation_id?: string;
  offset?: number;
  limit?: number;
}

export const interactionsApi = {
  list: (params?: ListInteractionsParams) =>
    fetchApi<InteractionResponse[]>('/interactions', { params }),

  getByConversationTimeline: (conversationId: string, offset = 0, limit = 100) =>
    fetchApi<InteractionResponse[]>(`/interactions/conversation/${conversationId}`, {
      params: { offset, limit },
    }),

  getByLeadTimeline: (leadId: string, offset = 0, limit = 100) =>
    fetchApi<InteractionResponse[]>(`/interactions/lead/${leadId}`, {
      params: { offset, limit },
    }),

  getById: (interactionId: string) =>
    fetchApi<InteractionResponse>(`/interactions/${interactionId}`),

  create: (data: InteractionCreateRequest) =>
    postApi<InteractionResponse>('/interactions', data),

  update: (interactionId: string, data: Partial<InteractionCreateRequest>) =>
    patchApi<InteractionResponse>(`/interactions/${interactionId}`, data),
};
