import { fetchApi, postApi, patchApi } from './client';
import { ConversationResponse, ConversationCreateRequest } from '@/types/api';

export interface ListConversationsParams {
  customer_id?: string;
  lead_id?: string;
  open_only?: boolean;
  offset?: number;
  limit?: number;
}

export const conversationsApi = {
  list: (params?: ListConversationsParams) =>
    fetchApi<ConversationResponse[]>('/conversations', { params }),

  getById: (conversationId: string) =>
    fetchApi<ConversationResponse>(`/conversations/${conversationId}`),

  create: (data: ConversationCreateRequest) =>
    postApi<ConversationResponse>('/conversations', data),

  update: (conversationId: string, data: Partial<ConversationCreateRequest>) =>
    patchApi<ConversationResponse>(`/conversations/${conversationId}`, data),

  linkLead: (conversationId: string, leadId: string | null) =>
    patchApi<ConversationResponse>(`/conversations/${conversationId}/lead`, { lead_id: leadId }),

  close: (conversationId: string, summary?: string) =>
    postApi<ConversationResponse>(`/conversations/${conversationId}/close`, { summary }),

  reopen: (conversationId: string) =>
    postApi<ConversationResponse>(`/conversations/${conversationId}/reopen`),
};
