import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { UserPlus, RefreshCw } from 'lucide-react';
import { enquiriesApi } from '@/api/enquiries';
import { leadsApi } from '@/api/leads';
import { EnquiryStatus, LeadSource } from '@/types/api';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { LeadSourceBadge, StatusBadge } from '@/components/common/StatusBadge';
import { formatDateTime } from '@/lib/utils';

export const EnquiriesPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<string>('');

  const [convertEnquiryId, setConvertEnquiryId] = useState<string | null>(null);
  const [convertStatusId, setConvertStatusId] = useState('');
  const [convertRequirement, setConvertRequirement] = useState('');

  const { data: enquiries = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['enquiries', selectedStatus, selectedSource],
    queryFn: () =>
      enquiriesApi.list({
        status: (selectedStatus as EnquiryStatus) || undefined,
        source: (selectedSource as LeadSource) || undefined,
      }),
  });

  const { data: leadStatuses = [], isLoading: loadingLeadStatuses } = useQuery({
    queryKey: ['lead-statuses'],
    queryFn: () => leadsApi.listStatuses(),
  });

  const openConvertModal = (enquiryId: string) => {
    const enquiry = enquiries.find((item) => item.id === enquiryId);

    if (!enquiry?.customer_id) {
      error(
        'Customer Required',
        'This enquiry must be linked to a customer before it can be converted to a lead.',
      );
      return;
    }

    const defaultStatus =
      leadStatuses.find((status) => status.key === 'NEW') ??
      leadStatuses[0];

    if (!defaultStatus) {
      error(
        'Lead Status Required',
        'No active lead lifecycle status is available for this organization.',
      );
      return;
    }

    setConvertEnquiryId(enquiryId);
    setConvertStatusId(defaultStatus.id);
    setConvertRequirement('');
  };

  // Convert to lead mutation
  const convertMutation = useMutation({
    mutationFn: (enquiryId: string) => {
      const enquiry = enquiries.find((item) => item.id === enquiryId);

      if (!enquiry?.customer_id) {
        throw new Error(
          'This enquiry must be linked to a customer before conversion.',
        );
      }

      if (!convertStatusId) {
        throw new Error('Select an initial lead status.');
      }

      return enquiriesApi.convertToLead(enquiryId, {
        status_id: convertStatusId,
        source: enquiry.source,
        original_source: enquiry.original_source ?? null,
        campaign_id: enquiry.campaign_id ?? null,
        ad_id: enquiry.ad_id ?? null,
        requirement: convertRequirement.trim() || null,
        original_enquiry: enquiry.message_text ?? null,
      });
    },
    onSuccess: (lead) => {
      success('Enquiry Converted', 'Successfully created a new sales lead.');
      setConvertEnquiryId(null);
      setConvertStatusId('');
      setConvertRequirement('');
      queryClient.invalidateQueries({ queryKey: ['enquiries'] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      navigate(`/app/leads/${lead.id}`);
    },
    onError: (err: any) => {
      error('Conversion Failed', err.message || 'Could not convert enquiry.');
    },
  });

  // Mark status mutation
  const markStatusMutation = useMutation({
    mutationFn: ({ enquiryId, status }: { enquiryId: string; status: EnquiryStatus }) => {
      if (status === EnquiryStatus.GENERAL_ENQUIRY) return enquiriesApi.markGeneralEnquiry(enquiryId);
      if (status === EnquiryStatus.NEEDS_REVIEW) return enquiriesApi.markNeedsReview(enquiryId);
      return enquiriesApi.updateStatus(enquiryId, status);
    },
    onSuccess: () => {
      success('Status Updated', 'Enquiry status updated.');
      queryClient.invalidateQueries({ queryKey: ['enquiries'] });
    },
    onError: (err: any) => {
      error('Update Failed', err.message || 'Unable to update enquiry.');
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Fetching omnichannel enquiries inbox..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Unable to load enquiries"
        description="Could not connect to the OmniLead backend."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Omnichannel Enquiries Inbox</h2>
          <p className="text-xs text-slate-500 mt-1">
            Inbound customer messages from WhatsApp, Instagram, and Meta Ads.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh Inbox
        </Button>
      </div>

      {/* Filter Bar */}
      <Card className="p-4 bg-white">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full sm:w-48 px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value="">All Statuses</option>
            {Object.values(EnquiryStatus).map((st) => (
              <option key={st} value={st}>
                {st.replace(/_/g, ' ')}
              </option>
            ))}
          </select>

          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="w-full sm:w-48 px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value="">All Channels</option>
            {Object.values(LeadSource).map((src) => (
              <option key={src} value={src}>
                {src}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Enquiries List */}
      {enquiries.length === 0 ? (
        <EmptyState
          title="Inbox is empty"
          description="No inbound enquiries match the selected channel or status filter."
        />
      ) : (
        <div className="space-y-4">
          {enquiries.map((enquiry) => (
            <Card key={enquiry.id} className="p-5 bg-white border border-slate-200 hover:border-slate-300 transition-all">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Channel & Customer Info */}
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <LeadSourceBadge source={enquiry.source} />
                    <h3 className="text-sm font-bold text-slate-900">
                      {enquiry.customer_name_raw || enquiry.contact_raw || 'Unknown Sender'}
                    </h3>
                    <StatusBadge status={enquiry.status} />
                  </div>

                  <p className="text-xs text-slate-700 mt-2 bg-slate-50 p-3 rounded-md border border-slate-100 italic">
                    "{enquiry.message_text || 'No message text available.'}"
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 mt-2">
                    <span>Received: {formatDateTime(enquiry.received_at)}</span>
                    {enquiry.contact_raw && <span>Contact: {enquiry.contact_raw}</span>}
                    {enquiry.customer_id && <span>Customer linked</span>}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      markStatusMutation.mutate({
                        enquiryId: enquiry.id,
                        status: EnquiryStatus.GENERAL_ENQUIRY,
                      })
                    }
                  >
                    General Enquiry
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    disabled={!enquiry.customer_id || loadingLeadStatuses}
                    onClick={() => openConvertModal(enquiry.id)}
                  >
                    <UserPlus className="w-4 h-4 mr-1.5" /> Convert to Lead
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Convert Modal */}
      <Modal
        isOpen={!!convertEnquiryId}
        onClose={() => {
          setConvertEnquiryId(null);
          setConvertStatusId('');
          setConvertRequirement('');
        }}
        title="Convert Inbound Enquiry to Lead"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-600">
            This will create a qualified sales lead in your pipeline and associate all previous message history.
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Initial Lead Status *
            </label>
            <select
              value={convertStatusId}
              onChange={(e) => setConvertStatusId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
            >
              <option value="">Select status</option>
              {leadStatuses.map((status) => (
                <option key={status.id} value={status.id}>
                  {status.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Requirement / Conversion Context
            </label>
            <textarea
              rows={3}
              value={convertRequirement}
              onChange={(e) => setConvertRequirement(e.target.value)}
              placeholder="e.g. Interested in premium tier enterprise package..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => {
                setConvertEnquiryId(null);
                setConvertStatusId('');
                setConvertRequirement('');
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!convertEnquiryId || !convertStatusId}
              onClick={() => convertEnquiryId && convertMutation.mutate(convertEnquiryId)}
              isLoading={convertMutation.isPending}
            >
              Confirm Conversion
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
