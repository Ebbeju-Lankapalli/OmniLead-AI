import { fetchApi, postApi } from './client';
import { NotificationResponse, NotificationCountResponse } from '@/types/api';

export interface ListNotificationsParams {
  unread_only?: boolean;
  offset?: number;
  limit?: number;
}

export const notificationsApi = {
  list: (params?: ListNotificationsParams) =>
    fetchApi<NotificationResponse[]>('/notifications', { params }),

  listUnread: (offset = 0, limit = 100) =>
    fetchApi<NotificationResponse[]>('/notifications/unread', {
      params: { offset, limit },
    }),

  getCounts: () =>
    fetchApi<NotificationCountResponse>('/notifications/counts'),

  markAllRead: () =>
    postApi<NotificationCountResponse>('/notifications/read-all'),

  getById: (notificationId: string) =>
    fetchApi<NotificationResponse>(`/notifications/${notificationId}`),

  markRead: (notificationId: string) =>
    postApi<NotificationResponse>(`/notifications/${notificationId}/read`),

  markUnread: (notificationId: string) =>
    postApi<NotificationResponse>(`/notifications/${notificationId}/unread`),
};
