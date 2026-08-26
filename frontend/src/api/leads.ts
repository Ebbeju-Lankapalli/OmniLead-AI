import { fetchApi, postApi, patchApi } from './client';
import {
  LeadResponse,
  LeadCreateRequest,
  LeadUpdate,
  LeadStatusOption,
} from '@/types/api';

export interface ListLeadsParams {
  status_id?: string;
  assigned_to_user_id?: string;
  customer_id?: string;
  product_id?: string;
  include_archived?: boolean;
  offset?: number;
  limit?: number;
}

export const leadsApi = {
  list: (params?: ListLeadsParams) =>
    fetchApi<LeadResponse[]>('/leads', { params }),

  listStatuses: () => fetchApi<LeadStatusOption[]>('/leads/statuses'),

  getPriorityQueue: (minimumPriorityScore = 0, limit = 50) =>
    fetchApi<LeadResponse[]>('/leads/priority-queue', {
      params: { minimum_priority_score: minimumPriorityScore, limit },
    }),

  getById: (leadId: string) =>
    fetchApi<LeadResponse>(`/leads/${leadId}`),

  create: (data: LeadCreateRequest) =>
    postApi<LeadResponse>('/leads', data),

  update: (leadId: string, data: LeadUpdate) =>
    patchApi<LeadResponse>(`/leads/${leadId}`, data),

  updateStatus: (leadId: string, statusId: string, closedAt?: string) =>
    patchApi<LeadResponse>(`/leads/${leadId}/status`, {
      status_id: statusId,
      closed_at: closedAt,
    }),

  updateAssignment: (leadId: string, assignedToUserId: string | null) =>
    patchApi<LeadResponse>(`/leads/${leadId}/assignment`, {
      assigned_to_user_id: assignedToUserId,
    }),

  archive: (leadId: string) =>
    postApi<LeadResponse>(`/leads/${leadId}/archive`),

  restore: (leadId: string) =>
    postApi<LeadResponse>(`/leads/${leadId}/restore`),
};
