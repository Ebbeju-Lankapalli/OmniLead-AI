import { apiClient } from './client';
import { CallUploadProcessingResponse } from '@/types/api';

export interface UploadCallParams {
  file: File;
  customer_id: string;
  lead_id?: string;
  conversation_id?: string;
  recorded_at?: string;
  metadata_json?: string;
}

export const callsApi = {
  uploadRecording: async (params: UploadCallParams): Promise<CallUploadProcessingResponse> => {
    const formData = new FormData();
    formData.append('file', params.file);
    formData.append('customer_id', params.customer_id);
    if (params.lead_id) formData.append('lead_id', params.lead_id);
    if (params.conversation_id) formData.append('conversation_id', params.conversation_id);
    if (params.recorded_at) formData.append('recorded_at', params.recorded_at);
    if (params.metadata_json) formData.append('metadata_json', params.metadata_json);

    const response = await apiClient.post<CallUploadProcessingResponse>('/calls/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },
};
