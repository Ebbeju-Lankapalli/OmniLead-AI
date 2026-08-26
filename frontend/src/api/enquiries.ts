import { fetchApi, postApi, patchApi } from './client';
import {
  EnquiryResponse,
  EnquiryCreateRequest,
  EnquiryConvertRequest,
  LeadResponse,
  EnquiryStatus,
  LeadSource,
} from '@/types/api';

export interface ListEnquiriesParams {
  status?: EnquiryStatus;
  source?: LeadSource;
  customer_id?: string;
  offset?: number;
  limit?: number;
}

export const enquiriesApi = {
  list: (params?: ListEnquiriesParams) =>
    fetchApi<EnquiryResponse[]>('/enquiries', { params }),

  listReviewQueue: (offset = 0, limit = 100) =>
    fetchApi<EnquiryResponse[]>('/enquiries/review-queue', {
      params: { offset, limit },
    }),

  getById: (enquiryId: string) =>
    fetchApi<EnquiryResponse>(`/enquiries/${enquiryId}`),

  create: (data: EnquiryCreateRequest) =>
    postApi<EnquiryResponse>('/enquiries', data),

  updateStatus: (enquiryId: string, status: EnquiryStatus, processingError?: string) =>
    patchApi<EnquiryResponse>(`/enquiries/${enquiryId}/status`, {
      status,
      processing_error: processingError,
    }),

  markNeedsReview: (enquiryId: string) =>
    postApi<EnquiryResponse>(`/enquiries/${enquiryId}/needs-review`),

  markAiAnalyzed: (enquiryId: string) =>
    postApi<EnquiryResponse>(`/enquiries/${enquiryId}/ai-analyzed`),

  markGeneralEnquiry: (enquiryId: string) =>
    postApi<EnquiryResponse>(`/enquiries/${enquiryId}/general-enquiry`),

  convertToLead: (enquiryId: string, data: EnquiryConvertRequest) =>
    postApi<LeadResponse>(`/enquiries/${enquiryId}/convert`, data),
};
