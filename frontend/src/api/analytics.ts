import { fetchApi } from './client';
import { AnalyticsResponse } from '@/types/api';

export const analyticsApi = {
  getAnalytics: (startDate: string, endDate: string) =>
    fetchApi<AnalyticsResponse>('/analytics', {
      params: { start_date: startDate, end_date: endDate },
    }),
};
