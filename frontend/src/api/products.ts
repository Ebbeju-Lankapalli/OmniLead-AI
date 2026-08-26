import { fetchApi, postApi, patchApi } from './client';
import { ProductResponse, ProductCreateRequest, ProductUpdate } from '@/types/api';

export interface ListProductsParams {
  active_only?: boolean;
  category?: string;
  offset?: number;
  limit?: number;
}

export const productsApi = {
  list: (params?: ListProductsParams) =>
    fetchApi<ProductResponse[]>('/products', { params }),

  search: (q: string, activeOnly = true, limit = 20) =>
    fetchApi<ProductResponse[]>('/products/search', {
      params: { q, active_only: activeOnly, limit },
    }),

  getById: (productId: string) =>
    fetchApi<ProductResponse>(`/products/${productId}`),

  create: (data: ProductCreateRequest) =>
    postApi<ProductResponse>('/products', data),

  update: (productId: string, data: ProductUpdate) =>
    patchApi<ProductResponse>(`/products/${productId}`, data),

  activate: (productId: string) =>
    postApi<ProductResponse>(`/products/${productId}/activate`),

  deactivate: (productId: string) =>
    postApi<ProductResponse>(`/products/${productId}/deactivate`),
};
