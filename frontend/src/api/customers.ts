import { fetchApi, postApi, patchApi } from './client';
import { CustomerResponse, CustomerCreateRequest, CustomerUpdate } from '@/types/api';

export interface ListCustomersParams {
  include_archived?: boolean;
  offset?: number;
  limit?: number;
}

export const customersApi = {
  list: (params?: ListCustomersParams) =>
    fetchApi<CustomerResponse[]>('/customers', { params }),

  search: (query: string, includeArchived = false, limit = 20) =>
    fetchApi<CustomerResponse[]>('/customers/search', {
      params: { query, include_archived: includeArchived, limit },
    }),

  getById: (customerId: string) =>
    fetchApi<CustomerResponse>(`/customers/${customerId}`),

  create: (data: CustomerCreateRequest) =>
    postApi<CustomerResponse>('/customers', data),

  update: (customerId: string, data: CustomerUpdate) =>
    patchApi<CustomerResponse>(`/customers/${customerId}`, data),

  archive: (customerId: string) =>
    postApi<CustomerResponse>(`/customers/${customerId}/archive`),

  restore: (customerId: string) =>
    postApi<CustomerResponse>(`/customers/${customerId}/restore`),
};
