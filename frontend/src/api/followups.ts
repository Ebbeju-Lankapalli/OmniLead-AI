import { fetchApi, postApi, patchApi } from './client';
import {
  FollowUpResponse,
  FollowUpCreateRequest,
  FollowUpCompleteRequest,
  FollowUpRescheduleRequest,
  FollowUpUpdateRequest,
  FollowUpStatus,
} from '@/types/api';

export interface ListFollowUpsParams {
  status?: FollowUpStatus;
  lead_id?: string;
  customer_id?: string;
  assigned_to_user_id?: string;
  offset?: number;
  limit?: number;
}

export const followupsApi = {
  list: (params?: ListFollowUpsParams) =>
    fetchApi<FollowUpResponse[]>('/followups', { params }),

  assignedToMe: (offset = 0, limit = 100) =>
    fetchApi<FollowUpResponse[]>('/followups/assigned-to-me', {
      params: { offset, limit },
    }),

  listDue: (dueAt: string, limit = 100) =>
    fetchApi<FollowUpResponse[]>('/followups/due', {
      params: { due_at: dueAt, limit },
    }),

  listOverdue: (nowStr: string, limit = 100) =>
    fetchApi<FollowUpResponse[]>('/followups/overdue', {
      params: { now: nowStr, limit },
    }),

  getById: (followupId: string) =>
    fetchApi<FollowUpResponse>(`/followups/${followupId}`),

  create: (data: FollowUpCreateRequest) =>
    postApi<FollowUpResponse>('/followups', data),

  update: (followupId: string, data: FollowUpUpdateRequest) =>
    patchApi<FollowUpResponse>(`/followups/${followupId}`, data),

  complete: (followupId: string, data: FollowUpCompleteRequest) =>
    postApi<FollowUpResponse>(`/followups/${followupId}/complete`, data),

  cancel: (followupId: string) =>
    postApi<FollowUpResponse>(`/followups/${followupId}/cancel`),

  reschedule: (followupId: string, data: FollowUpRescheduleRequest) =>
    postApi<FollowUpResponse>(`/followups/${followupId}/reschedule`, data),
};
