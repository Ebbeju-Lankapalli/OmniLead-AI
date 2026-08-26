import { postApi, fetchApi } from './client';
import { AuthSessionResponse, AuthTokenResponse } from '@/types/api';

export interface LoginParams {
  email: string;
  password: string;
}

export interface RegisterParams {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
  organization_slug: string;
}

export const authApi = {
  login: (data: LoginParams) => postApi<AuthSessionResponse>('/auth/login', data),
  register: (data: RegisterParams) => postApi<AuthSessionResponse>('/auth/register', data),
  getMe: () => fetchApi<AuthSessionResponse>('/auth/me'),
  refreshSession: (refreshToken: string) =>
    postApi<AuthTokenResponse>('/auth/refresh', { refresh_token: refreshToken }),
};
