import { fetchApi } from './client';
import { DashboardResponse } from '@/types/api';

export const dashboardApi = {
  getDashboard: () => fetchApi<DashboardResponse>('/dashboard'),
};
