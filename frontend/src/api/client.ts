import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { OmniLeadApiError } from '@/types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let getAccessTokenFn: (() => string | null) | null = null;

export function setAccessTokenGetter(fn: () => string | null) {
  getAccessTokenFn = fn;
}

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessTokenFn ? getAccessTokenFn() : localStorage.getItem('omnilead_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<OmniLeadApiError & { detail?: string | any[] }>) => {
    if (error.response) {
      const apiError = error.response.data;
      if (apiError && apiError.error) {
        const msg = apiError.error.message;
        const detailsStr = apiError.error.details ? ` (${JSON.stringify(apiError.error.details)})` : '';
        return Promise.reject(new Error(msg ? `${msg}${detailsStr}` : 'API request failed'));
      }
      if (apiError && apiError.detail) {
        if (typeof apiError.detail === 'string') {
          return Promise.reject(new Error(apiError.detail));
        }
        if (Array.isArray(apiError.detail)) {
          const msg = apiError.detail
            .map((d: any) => {
              const field = d.loc ? d.loc.filter((l: string) => l !== 'body').join('.') : '';
              return field ? `${field}: ${d.msg}` : d.msg;
            })
            .join('; ');
          return Promise.reject(new Error(msg || 'Validation failed'));
        }
      }
    }
    return Promise.reject(
      new Error(error.message || 'Could not complete the API request')
    );
  }
);

export async function fetchApi<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.get<T>(url, config);
  return response.data;
}

export async function postApi<T, D = any>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
}

export async function patchApi<T, D = any>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.patch<T>(url, data, config);
  return response.data;
}

export async function deleteApi<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.delete<T>(url, config);
  return response.data;
}
