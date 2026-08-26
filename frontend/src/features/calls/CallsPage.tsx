import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PhoneCall, UploadCloud, FileAudio, CheckCircle2, Sparkles } from 'lucide-react';
import { callsApi } from '@/api/calls';
import { customersApi } from '@/api/customers';
import { leadsApi } from '@/api/leads';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Select } from '@/components/ui/Select';
import { EmptyState } from '@/components/common/EmptyState';

export const CallsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [selectedLeadId, setSelectedLeadId] = useState('');
  const [fileError, setFileError] = useState('');

  // Queries
  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customersApi.list(),
  });

  const { data: leads = [] } = useQuery({
    queryKey: ['leads'],
    queryFn: () => leadsApi.list(),
  });

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile || !selectedCustomerId) {
        throw new Error('Please select a valid audio file and customer.');
      }
      return callsApi.uploadRecording({
        file: selectedFile,
        customer_id: selectedCustomerId,
        lead_id: selectedLeadId || undefined,
      });
    },
    onSuccess: (res) => {
      success('Call Uploaded & Transcribing', `Status: ${res.transcription_status || 'Submitted to Whisper'}`);
      setShowUploadModal(false);
      setSelectedFile(null);
      setSelectedCustomerId('');
      setSelectedLeadId('');
      queryClient.invalidateQueries({ queryKey: ['calls'] });
    },
    onError: (err: any) => {
      error('Upload Failed', err.message || 'Could not process audio upload.');
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFileError('');
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-m4a', 'audio/m4a', 'audio/ogg'];
      if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|ogg)$/i)) {
        setFileError('Invalid file type. Supported formats: .mp3, .wav, .m4a, .ogg');
        setSelectedFile(null);
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        setFileError('File size exceeds 50MB limit.');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Call Intelligence & Transcripts</h2>
          <p className="text-xs text-slate-500 mt-1">
            Automated Whisper transcription, sentiment analysis, and action item extraction.
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={() => setShowUploadModal(true)}>
          <UploadCloud className="w-4 h-4 mr-1.5" /> Upload Call Recording
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-white border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <PhoneCall className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400">Speech Engine</span>
              <p className="text-sm font-bold text-slate-900">Faster-Whisper Large-v3</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-white border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400">AI Extraction</span>
              <p className="text-sm font-bold text-slate-900">Gemini Intent & Objections</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-white border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400">Max File Size</span>
              <p className="text-sm font-bold text-slate-900">50 MB (.mp3, .wav, .m4a)</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Transcripts List */}
      <Card className="p-6 bg-white space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Processed Call Intelligence</h3>
        <EmptyState
          title="No call recordings uploaded yet"
          description="Upload an audio file to generate automated transcriptions and sales action items."
          actionLabel="Upload Audio Recording"
          onAction={() => setShowUploadModal(true)}
        />
      </Card>

      {/* Upload Modal */}
      <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} title="Upload Call Recording">
        <div className="space-y-4">
          <Select
            label="Select Associated Customer *"
            value={selectedCustomerId}
            onChange={(e) => setSelectedCustomerId(e.target.value)}
            options={customers.map((c) => ({
              label: `${c.full_name} (${c.company_name || c.primary_phone || 'Customer'})`,
              value: c.id,
            }))}
            required
          />

          <Select
            label="Associated Lead (Optional)"
            value={selectedLeadId}
            onChange={(e) => setSelectedLeadId(e.target.value)}
            options={leads.map((l) => ({
              label: `${l.customer?.full_name || 'Lead'} - ${l.product?.name || 'General'}`,
              value: l.id,
            }))}
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Audio Recording File *</label>
            <input
              type="file"
              accept=".mp3,.wav,.m4a,.ogg"
              onChange={handleFileChange}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900"
            />
            {fileError && <p className="text-xs text-rose-600 font-semibold mt-1">{fileError}</p>}
            {selectedFile && (
              <p className="text-xs text-emerald-700 font-semibold mt-1 flex items-center gap-1">
                <FileAudio className="w-3.5 h-3.5" /> Ready: {selectedFile.name} (
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowUploadModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!selectedFile || !selectedCustomerId}
              onClick={() => uploadMutation.mutate()}
              isLoading={uploadMutation.isPending}
            >
              Upload & Transcribe
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
