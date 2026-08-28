import { apiClient } from './client';
import {
  CallIntelligenceResponse,
  CallUploadProcessingResponse,
} from '@/types/api';

export interface CallRecordingSummary {
  id: string;
  customer_id: string;
  lead_id?: string | null;
  conversation_id?: string | null;
  original_filename: string;
  duration_seconds?: number | null;

  transcription_status:
    | 'PENDING'
    | 'PROCESSING'
    | 'COMPLETED'
    | 'FAILED';

  transcript_language?: string | null;
  transcript?: string | null;
  recorded_at?: string | null;
  uploaded_at: string;

  /**
   * Persisted AI intelligence generated from
   * the completed call transcript.
   */
  intelligence?: CallIntelligenceResponse | null;
}

export interface UploadCallParams {
  file: File;
  customer_id: string;
  lead_id?: string;
  conversation_id?: string;
  recorded_at?: string;
  metadata_json?: string;
}

export const callsApi = {
  /**
   * Get all uploaded call recordings.
   *
   * Each recording may contain the latest
   * persisted CALL_ANALYSIS intelligence.
   */
  list: async (): Promise<CallRecordingSummary[]> => {
    const response =
      await apiClient.get<CallRecordingSummary[]>(
        '/calls'
      );

    return response.data;
  },

  /**
   * Upload a call recording and process it
   * through Whisper + Gemini.
   */
  uploadRecording: async (
    params: UploadCallParams
  ): Promise<CallUploadProcessingResponse> => {
    const formData = new FormData();

    formData.append(
      'file',
      params.file
    );

    formData.append(
      'customer_id',
      params.customer_id
    );

    if (params.lead_id) {
      formData.append(
        'lead_id',
        params.lead_id
      );
    }

    if (params.conversation_id) {
      formData.append(
        'conversation_id',
        params.conversation_id
      );
    }

    if (params.recorded_at) {
      formData.append(
        'recorded_at',
        params.recorded_at
      );
    }

    if (params.metadata_json) {
      formData.append(
        'metadata_json',
        params.metadata_json
      );
    }

    const response =
      await apiClient.post<CallUploadProcessingResponse>(
        '/calls/upload',
        formData,
        {
          headers: {
            'Content-Type':
              'multipart/form-data',
          },
        }
      );

    return response.data;
  },
};