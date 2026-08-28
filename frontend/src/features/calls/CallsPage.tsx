import React, { useState } from 'react';
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import {
  PhoneCall,
  UploadCloud,
  FileAudio,
  CheckCircle2,
  Sparkles,
  RefreshCw,
  Target,
  MessageSquare,
  AlertTriangle,
  Handshake,
  ListChecks,
  HelpCircle,
  Clock3,
  ShieldCheck,
} from 'lucide-react';

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
  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);
  const [selectedCustomerId, setSelectedCustomerId] =
    useState('');
  const [selectedLeadId, setSelectedLeadId] =
    useState('');
  const [fileError, setFileError] = useState('');

  // ---------------------------------------------------------------------------
  // Customers
  // ---------------------------------------------------------------------------

  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customersApi.list(),
  });

  // ---------------------------------------------------------------------------
  // Leads
  // ---------------------------------------------------------------------------

  const { data: leads = [] } = useQuery({
    queryKey: ['leads'],
    queryFn: () => leadsApi.list(),
  });

  // ---------------------------------------------------------------------------
  // Call Recordings
  // ---------------------------------------------------------------------------

  const {
    data: calls = [],
    isLoading: callsLoading,
    isError: callsError,
    refetch: refetchCalls,
  } = useQuery({
    queryKey: ['calls'],
    queryFn: () => callsApi.list(),
  });

  // ---------------------------------------------------------------------------
  // Upload Call Recording
  // ---------------------------------------------------------------------------

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile || !selectedCustomerId) {
        throw new Error(
          'Please select a valid audio file and customer.'
        );
      }

      return callsApi.uploadRecording({
        file: selectedFile,
        customer_id: selectedCustomerId,
        lead_id: selectedLeadId || undefined,
      });
    },

    onSuccess: (res) => {
      success(
        'Call Uploaded & Transcribing',
        `Status: ${
          res.transcription_status ||
          'Submitted to Whisper'
        }`
      );

      setShowUploadModal(false);
      setSelectedFile(null);
      setSelectedCustomerId('');
      setSelectedLeadId('');
      setFileError('');

      queryClient.invalidateQueries({
        queryKey: ['calls'],
      });
    },

    onError: (err: any) => {
      error(
        'Upload Failed',
        err.message ||
          'Could not process audio upload.'
      );
    },
  });

  // ---------------------------------------------------------------------------
  // File Validation
  // ---------------------------------------------------------------------------

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFileError('');

    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];

      const validTypes = [
        'audio/mpeg',
        'audio/mp3',
        'audio/wav',
        'audio/x-m4a',
        'audio/m4a',
        'audio/ogg',
      ];

      if (
        !validTypes.includes(file.type) &&
        !file.name.match(
          /\.(mp3|wav|m4a|ogg)$/i
        )
      ) {
        setFileError(
          'Invalid file type. Supported formats: .mp3, .wav, .m4a, .ogg'
        );

        setSelectedFile(null);
        return;
      }

      if (file.size > 50 * 1024 * 1024) {
        setFileError(
          'File size exceeds 50MB limit.'
        );

        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
    }
  };

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  const formatDuration = (
    seconds: number | null | undefined
  ) => {
    if (seconds == null) {
      return 'Duration unavailable';
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(
      seconds % 60
    );

    return `${minutes}:${remainingSeconds
      .toString()
      .padStart(2, '0')}`;
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-50 text-emerald-700';

      case 'FAILED':
        return 'bg-rose-50 text-rose-700';

      case 'PROCESSING':
        return 'bg-indigo-50 text-indigo-700';

      default:
        return 'bg-amber-50 text-amber-700';
    }
  };

  const getIntentClass = (
    intent: string | null | undefined
  ) => {
    const normalized = (
      intent || ''
    ).toUpperCase();

    if (
      normalized.includes('HIGH') ||
      normalized.includes('STRONG')
    ) {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }

    if (
      normalized.includes('MEDIUM') ||
      normalized.includes('MODERATE')
    ) {
      return 'bg-amber-50 text-amber-700 border-amber-200';
    }

    if (
      normalized.includes('LOW') ||
      normalized.includes('NONE')
    ) {
      return 'bg-slate-100 text-slate-600 border-slate-200';
    }

    return 'bg-indigo-50 text-indigo-700 border-indigo-200';
  };

  const getSentimentClass = (
    sentiment: string | null | undefined
  ) => {
    const normalized = (
      sentiment || ''
    ).toUpperCase();

    if (
      normalized.includes('POSITIVE')
    ) {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }

    if (
      normalized.includes('NEGATIVE')
    ) {
      return 'bg-rose-50 text-rose-700 border-rose-200';
    }

    if (
      normalized.includes('NEUTRAL')
    ) {
      return 'bg-slate-100 text-slate-600 border-slate-200';
    }

    return 'bg-indigo-50 text-indigo-700 border-indigo-200';
  };

  const formatConfidence = (
    confidence: number | null | undefined
  ) => {
    if (confidence == null) {
      return 'N/A';
    }

    return `${Math.round(
      confidence * 100
    )}%`;
  };

  const renderList = (
    items: string[] | undefined,
    emptyText: string
  ) => {
    if (!items || items.length === 0) {
      return (
        <p className="text-xs text-slate-400">
          {emptyText}
        </p>
      );
    }

    return (
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li
            key={`${item}-${index}`}
            className="flex items-start gap-2 text-sm text-slate-700"
          >
            <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
            <span className="leading-5">
              {item}
            </span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="space-y-6">

      {/* ------------------------------------------------------------------ */}
      {/* Header */}
      {/* ------------------------------------------------------------------ */}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Call Intelligence & Transcripts
          </h2>

          <p className="text-xs text-slate-500 mt-1">
            Automated Whisper transcription,
            sentiment analysis, and sales intelligence
            extraction.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() =>
            setShowUploadModal(true)
          }
        >
          <UploadCloud className="w-4 h-4 mr-1.5" />
          Upload Call Recording
        </Button>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Overview Cards */}
      {/* ------------------------------------------------------------------ */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        <Card className="p-4 bg-white border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <PhoneCall className="w-5 h-5" />
            </div>

            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400">
                Speech Engine
              </span>

              <p className="text-sm font-bold text-slate-900">
                Faster-Whisper Large-v3
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-white border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>

            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400">
                AI Extraction
              </span>

              <p className="text-sm font-bold text-slate-900">
                Gemini Intent & Objections
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-white border border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>

            <div>
              <span className="text-[11px] font-semibold uppercase text-slate-400">
                Max File Size
              </span>

              <p className="text-sm font-bold text-slate-900">
                50 MB (.mp3, .wav, .m4a)
              </p>
            </div>
          </div>
        </Card>

      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Processed Calls */}
      {/* ------------------------------------------------------------------ */}

      <Card className="p-6 bg-white space-y-4">

        <div className="flex items-center justify-between">

          <h3 className="text-sm font-bold text-slate-900">
            Processed Call Intelligence
          </h3>

          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              refetchCalls()
            }
            disabled={callsLoading}
          >
            <RefreshCw
              className={`w-4 h-4 mr-1.5 ${
                callsLoading
                  ? 'animate-spin'
                  : ''
              }`}
            />

            Refresh
          </Button>

        </div>

        {/* Loading */}

        {callsLoading && (
          <div className="py-12 text-center">

            <RefreshCw className="w-6 h-6 mx-auto mb-3 text-slate-400 animate-spin" />

            <p className="text-sm text-slate-500">
              Loading call recordings...
            </p>

          </div>
        )}

        {/* Error */}

        {!callsLoading &&
          callsError && (
            <div className="py-10 text-center">

              <p className="text-sm font-semibold text-rose-600">
                Could not load call recordings.
              </p>

              <p className="text-xs text-slate-500 mt-1">
                Check that the backend is running
                and try again.
              </p>

              <Button
                variant="outline"
                size="sm"
                className="mt-4"
                onClick={() =>
                  refetchCalls()
                }
              >
                Try Again
              </Button>

            </div>
          )}

        {/* Empty */}

        {!callsLoading &&
          !callsError &&
          calls.length === 0 && (
            <EmptyState
              title="No call recordings uploaded yet"
              description="Upload an audio file to generate automated transcriptions and sales action items."
              actionLabel="Upload Audio Recording"
              onAction={() =>
                setShowUploadModal(true)
              }
            />
          )}

        {/* Calls */}

        {!callsLoading &&
          !callsError &&
          calls.length > 0 && (
            <div className="space-y-5">

              {calls.map((call) => {

                const intelligence =
                  call.intelligence;

                return (
                  <div
                    key={call.id}
                    className="border border-slate-200 rounded-xl bg-white overflow-hidden"
                  >

                    {/* ---------------------------------------------------- */}
                    {/* Call Header */}
                    {/* ---------------------------------------------------- */}

                    <div className="p-4 bg-slate-50 border-b border-slate-200">

                      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">

                        <div className="flex items-center gap-3">

                          <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center shrink-0">
                            <FileAudio className="w-5 h-5" />
                          </div>

                          <div>

                            <p className="text-sm font-bold text-slate-900">
                              {call.original_filename}
                            </p>

                            <div className="flex flex-wrap gap-2 mt-1 text-[11px] text-slate-500">

                              <span>
                                {call.transcript_language ||
                                  'Language unavailable'}
                              </span>

                              <span>•</span>

                              <span>
                                {formatDuration(
                                  call.duration_seconds
                                )}
                              </span>

                              <span>•</span>

                              <span>
                                {new Date(
                                  call.uploaded_at
                                ).toLocaleString()}
                              </span>

                            </div>

                          </div>

                        </div>

                        <span
                          className={`self-start md:self-center px-2.5 py-1 rounded text-[10px] font-bold uppercase ${getStatusClass(
                            call.transcription_status
                          )}`}
                        >
                          {call.transcription_status}
                        </span>

                      </div>

                    </div>

                    {/* ---------------------------------------------------- */}
                    {/* Completed Call */}
                    {/* ---------------------------------------------------- */}

                    {call.transcription_status ===
                      'COMPLETED' && (
                      <div className="p-4 space-y-5">

                        {/* ------------------------------------------------ */}
                        {/* AI Intelligence */}
                        {/* ------------------------------------------------ */}

                        {intelligence && (
                          <div className="space-y-5">

                            {/* AI Summary */}

                            <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-4">

                              <div className="flex items-center gap-2 mb-2">

                                <Sparkles className="w-4 h-4 text-indigo-600" />

                                <h4 className="text-xs font-bold uppercase tracking-wide text-indigo-700">
                                  AI Call Summary
                                </h4>

                              </div>

                              <p className="text-sm text-slate-700 leading-6">
                                {intelligence.summary ||
                                  'No AI summary available.'}
                              </p>

                            </div>

                            {/* Key Metrics */}

                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">

                              {/* Purchase Intent */}

                              <div className="border border-slate-200 rounded-lg p-3">

                                <div className="flex items-center gap-2 mb-2">

                                  <Target className="w-4 h-4 text-indigo-600" />

                                  <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                                    Purchase Intent
                                  </span>

                                </div>

                                <span
                                  className={`inline-flex px-2.5 py-1 rounded border text-xs font-bold uppercase ${getIntentClass(
                                    intelligence.purchase_intent
                                  )}`}
                                >
                                  {intelligence.purchase_intent ||
                                    'Unknown'}
                                </span>

                              </div>

                              {/* Sentiment */}

                              <div className="border border-slate-200 rounded-lg p-3">

                                <div className="flex items-center gap-2 mb-2">

                                  <MessageSquare className="w-4 h-4 text-indigo-600" />

                                  <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                                    Sentiment
                                  </span>

                                </div>

                                <span
                                  className={`inline-flex px-2.5 py-1 rounded border text-xs font-bold uppercase ${getSentimentClass(
                                    intelligence.sentiment
                                  )}`}
                                >
                                  {intelligence.sentiment ||
                                    'Unknown'}
                                </span>

                              </div>

                              {/* Confidence */}

                              <div className="border border-slate-200 rounded-lg p-3">

                                <div className="flex items-center gap-2 mb-2">

                                  <ShieldCheck className="w-4 h-4 text-emerald-600" />

                                  <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                                    AI Confidence
                                  </span>

                                </div>

                                <p className="text-lg font-bold text-slate-900">
                                  {formatConfidence(
                                    intelligence.confidence
                                  )}
                                </p>

                              </div>

                              {/* Review */}

                              <div className="border border-slate-200 rounded-lg p-3">

                                <div className="flex items-center gap-2 mb-2">

                                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />

                                  <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                                    Review Status
                                  </span>

                                </div>

                                <p
                                  className={`text-xs font-bold ${
                                    intelligence.requires_review
                                      ? 'text-amber-700'
                                      : 'text-emerald-700'
                                  }`}
                                >
                                  {intelligence.requires_review
                                    ? 'Requires Human Review'
                                    : 'No Review Required'}
                                </p>

                              </div>

                            </div>

                            {/* Requirement */}

                            {intelligence.requirement && (
                              <div className="border border-slate-200 rounded-xl p-4">

                                <div className="flex items-center gap-2 mb-2">

                                  <ListChecks className="w-4 h-4 text-indigo-600" />

                                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-400">
                                    Customer Requirement
                                  </h4>

                                </div>

                                <p className="text-sm text-slate-700 leading-6">
                                  {intelligence.requirement}
                                </p>

                              </div>
                            )}

                            {/* Intelligence Lists */}

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

                              {/* Objections */}

                              <div className="border border-slate-200 rounded-xl p-4">

                                <div className="flex items-center gap-2 mb-3">

                                  <AlertTriangle className="w-4 h-4 text-rose-500" />

                                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500">
                                    Objections
                                  </h4>

                                </div>

                                {renderList(
                                  intelligence.objections,
                                  'No objections identified.'
                                )}

                              </div>

                              {/* Commitments */}

                              <div className="border border-slate-200 rounded-xl p-4">

                                <div className="flex items-center gap-2 mb-3">

                                  <Handshake className="w-4 h-4 text-emerald-600" />

                                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500">
                                    Commitments
                                  </h4>

                                </div>

                                {renderList(
                                  intelligence.commitments,
                                  'No commitments identified.'
                                )}

                              </div>

                              {/* Action Items */}

                              <div className="border border-slate-200 rounded-xl p-4">

                                <div className="flex items-center gap-2 mb-3">

                                  <ListChecks className="w-4 h-4 text-indigo-600" />

                                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500">
                                    Action Items
                                  </h4>

                                </div>

                                {renderList(
                                  intelligence.action_items,
                                  'No action items identified.'
                                )}

                              </div>

                              {/* Customer Questions */}

                              <div className="border border-slate-200 rounded-xl p-4">

                                <div className="flex items-center gap-2 mb-3">

                                  <HelpCircle className="w-4 h-4 text-amber-600" />

                                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500">
                                    Customer Questions
                                  </h4>

                                </div>

                                {renderList(
                                  intelligence.customer_questions,
                                  'No customer questions identified.'
                                )}

                              </div>

                            </div>

                            {/* Key Moments */}

                            <div className="border border-slate-200 rounded-xl p-4">

                              <div className="flex items-center gap-2 mb-3">

                                <Clock3 className="w-4 h-4 text-indigo-600" />

                                <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500">
                                  Key Moments
                                </h4>

                              </div>

                              {renderList(
                                intelligence.key_moments,
                                'No key moments identified.'
                              )}

                            </div>

                            {/* Analysis ID */}

                            <div className="text-[10px] text-slate-400">
                              Analysis ID:{' '}
                              {intelligence.analysis_id}
                            </div>

                          </div>
                        )}

                        {/* ------------------------------------------------ */}
                        {/* Transcript */}
                        {/* ------------------------------------------------ */}

                        <div>

                          <h4 className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-2">
                            Transcript
                          </h4>

                          <div className="bg-slate-50 border border-slate-100 rounded-lg p-4">

                            <p className="text-sm text-slate-700 leading-6 whitespace-pre-wrap">
                              {call.transcript ||
                                'No transcript available.'}
                            </p>

                          </div>

                        </div>

                      </div>
                    )}

                    {/* ---------------------------------------------------- */}
                    {/* Processing */}
                    {/* ---------------------------------------------------- */}

                    {call.transcription_status ===
                      'PROCESSING' && (
                      <div className="p-5">

                        <div className="flex items-center gap-3 text-indigo-700">

                          <RefreshCw className="w-5 h-5 animate-spin" />

                          <div>

                            <p className="text-sm font-semibold">
                              Transcription in progress
                            </p>

                            <p className="text-xs text-slate-500 mt-1">
                              Whisper is processing this
                              recording.
                            </p>

                          </div>

                        </div>

                      </div>
                    )}

                    {/* ---------------------------------------------------- */}
                    {/* Pending */}
                    {/* ---------------------------------------------------- */}

                    {call.transcription_status ===
                      'PENDING' && (
                      <div className="p-5">

                        <p className="text-sm font-semibold text-amber-700">
                          Waiting for transcription
                        </p>

                      </div>
                    )}

                    {/* ---------------------------------------------------- */}
                    {/* Failed */}
                    {/* ---------------------------------------------------- */}

                    {call.transcription_status ===
                      'FAILED' && (
                      <div className="p-5">

                        <p className="text-sm font-semibold text-rose-700">
                          Transcription failed
                        </p>

                      </div>
                    )}

                  </div>
                );
              })}

            </div>
          )}

      </Card>

      {/* ------------------------------------------------------------------ */}
      {/* Upload Modal */}
      {/* ------------------------------------------------------------------ */}

      <Modal
        isOpen={showUploadModal}
        onClose={() =>
          setShowUploadModal(false)
        }
        title="Upload Call Recording"
      >

        <div className="space-y-4">

          {/* Customer */}

          <Select
            label="Select Associated Customer *"
            value={selectedCustomerId}
            onChange={(e) =>
              setSelectedCustomerId(
                e.target.value
              )
            }
            options={customers.map((c) => ({
              label: `${c.full_name} (${
                c.company_name ||
                c.primary_phone ||
                'Customer'
              })`,
              value: c.id,
            }))}
            required
          />

          {/* Lead */}

          <Select
            label="Associated Lead (Optional)"
            value={selectedLeadId}
            onChange={(e) =>
              setSelectedLeadId(
                e.target.value
              )
            }
            options={leads.map((l) => ({
              label: `${
                l.customer?.full_name ||
                'Lead'
              } - ${
                l.product?.name ||
                'General'
              }`,
              value: l.id,
            }))}
          />

          {/* File */}

          <div>

            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Audio Recording File *
            </label>

            <input
              type="file"
              accept=".mp3,.wav,.m4a,.ogg"
              onChange={handleFileChange}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900"
            />

            {fileError && (
              <p className="text-xs text-rose-600 font-semibold mt-1">
                {fileError}
              </p>
            )}

            {selectedFile && (
              <p className="text-xs text-emerald-700 font-semibold mt-1 flex items-center gap-1">

                <FileAudio className="w-3.5 h-3.5" />

                Ready: {selectedFile.name} (
                {(
                  selectedFile.size /
                  (1024 * 1024)
                ).toFixed(2)}{' '}
                MB)

              </p>
            )}

          </div>

          {/* Buttons */}

          <div className="flex justify-end gap-2 pt-2">

            <Button
              variant="outline"
              onClick={() =>
                setShowUploadModal(false)
              }
            >
              Cancel
            </Button>

            <Button
              variant="primary"
              disabled={
                !selectedFile ||
                !selectedCustomerId
              }
              onClick={() =>
                uploadMutation.mutate()
              }
              isLoading={
                uploadMutation.isPending
              }
            >
              Upload & Transcribe
            </Button>

          </div>

        </div>

      </Modal>

    </div>
  );
};