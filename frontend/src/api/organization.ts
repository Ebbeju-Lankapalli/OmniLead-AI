import { fetchApi, patchApi } from './client';
import { OrganizationResponse, OrganizationUpdate } from '@/types/api';

export const organizationApi = {
  getCurrent: () => fetchApi<OrganizationResponse>('/organization'),
  updateCurrent: (data: OrganizationUpdate) => patchApi<OrganizationResponse>('/organization', data),
};
