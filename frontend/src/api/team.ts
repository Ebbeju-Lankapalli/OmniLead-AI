import { fetchApi, patchApi } from './client';
import { UserResponse, TeamMemberUpdate } from '@/types/api';

export interface ListTeamParams {
  active_only?: boolean;
  offset?: number;
  limit?: number;
}

export const teamApi = {
  list: (params?: ListTeamParams) =>
    fetchApi<UserResponse[]>('/users', { params }),

  getById: (userId: string) =>
    fetchApi<UserResponse>(`/users/${userId}`),

  update: (userId: string, data: TeamMemberUpdate) =>
    patchApi<UserResponse>(`/users/${userId}`, data),
};
