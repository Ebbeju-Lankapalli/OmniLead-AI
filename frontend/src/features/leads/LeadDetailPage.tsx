import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Sparkles,
  Tag,
  Plus,
  UserPlus,
} from 'lucide-react';
import { leadsApi } from '@/api/leads';
import { aiApi } from '@/api/ai';
import { followupsApi } from '@/api/followups';
import { interactionsApi } from '@/api/interactions';
import { teamApi } from '@/api/team';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Tabs } from '@/components/ui/Tabs';
import { Modal } from '@/components/ui/Modal';
import { Select } from '@/components/ui/Select';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { ScoreBreakdownCard } from '@/components/common/ScoreBreakdownCard';
import {
  StatusBadge,
  LeadSourceBadge,
  PurchaseIntentBadge,
  PriorityBadge,
} from '@/components/common/StatusBadge';
import { formatDateTime, formatDate } from '@/lib/utils';
import { FollowUpType } from '@/types/api';

export const LeadDetailPage: React.FC = () => {
  const { id: leadId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState('overview');
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showFollowupModal, setShowFollowupModal] = useState(false);

  const [selectedStatusId, setSelectedStatusId] = useState('');
  const [selectedUserId, setSelectedUserId] = useState('');

  // Follow-up form state
  const [followupType, setFollowupType] = useState<FollowUpType>(FollowUpType.CALL);
  const [scheduledAt, setScheduledAt] = useState('');
  const [notes, setNotes] = useState('');

  // Queries
  const { data: lead, isLoading, isError } = useQuery({
    queryKey: ['lead', leadId],
    queryFn: () => leadsApi.getById(leadId!),
    enabled: !!leadId,
  });

  const { data: statuses = [] } = useQuery({
    queryKey: ['lead-statuses'],
    queryFn: () => leadsApi.listStatuses(),
  });

  const { data: teamMembers = [] } = useQuery({
    queryKey: ['team', 'active'],
    queryFn: () => teamApi.list({ active_only: true }),
  });

  const { data: timeline = [] } = useQuery({
    queryKey: ['lead-timeline', leadId],
    queryFn: () => interactionsApi.getByLeadTimeline(leadId!),
    enabled: !!leadId,
  });

  const { data: followups = [] } = useQuery({
    queryKey: ['lead-followups', leadId],
    queryFn: () => followupsApi.list({ lead_id: leadId }),
    enabled: !!leadId,
  });

  // AI Re-analyze Mutation
  const aiAnalyzeMutation = useMutation({
    mutationFn: () =>
      aiApi.analyzeLead(
        leadId!,
        lead?.notes || 'Analyze lead timeline and qualification status',
        lead?.customer?.full_name || '',
        lead?.product?.name || '',
        '',
        true
      ),
    onSuccess: () => {
      success('AI Analysis Completed', 'Updated lead qualification and priority scores.');
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] });
    },
    onError: (err: any) => {
      error('AI Analysis Failed', err.message || 'Could not execute Gemini AI analysis.');
    },
  });

  // Status Change Mutation
  const updateStatusMutation = useMutation({
    mutationFn: (statusId: string) => leadsApi.updateStatus(leadId!, statusId),
    onSuccess: () => {
      success('Status Updated', 'Lead status has been changed.');
      setShowStatusModal(false);
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] });
    },
    onError: (err: any) => {
      error('Update Failed', err.message || 'Unable to update status.');
    },
  });

  // Reassign Mutation
  const reassignMutation = useMutation({
    mutationFn: (userId: string | null) => leadsApi.updateAssignment(leadId!, userId),
    onSuccess: (_, userId) => {
      success(
        'Assignment Updated',
        userId ? 'Lead salesperson assigned.' : 'Lead is now unassigned.',
      );
      setShowAssignModal(false);
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] });
    },
    onError: (err: any) => {
      error('Assignment Failed', err.message || 'Unable to update assignment.');
    },
  });

  // Create Followup Mutation
  const createFollowupMutation = useMutation({
    mutationFn: () => {
      if (!leadId) {
        throw new Error('Lead ID is missing.');
      }

      if (!lead?.customer_id) {
        throw new Error('This lead is not linked to a customer.');
      }

      if (!lead.assigned_to_user_id) {
        throw new Error('Assign this lead to a salesperson before scheduling a follow-up.');
      }

      if (!scheduledAt) {
        throw new Error('Select a follow-up date and time.');
      }

      return followupsApi.create({
        lead_id: leadId,
        customer_id: lead.customer_id,
        assigned_to_user_id: lead.assigned_to_user_id,
        followup_type: followupType,
        scheduled_at: new Date(scheduledAt).toISOString(),
        notes: notes.trim() || null,
      });
    },
    onSuccess: () => {
      success('Follow-Up Scheduled', 'New follow-up activity added.');
      setShowFollowupModal(false);
      queryClient.invalidateQueries({ queryKey: ['lead-followups', leadId] });
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] });
    },
    onError: (err: any) => {
      error('Follow-Up Failed', err.message || 'Could not schedule follow-up.');
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Fetching detailed lead intelligence profile..." />;
  }

  if (isError || !lead) {
    return (
      <EmptyState
        title="Lead not found"
        description="The requested lead does not exist or you do not have permission to view it."
        actionLabel="Back to Leads"
        onAction={() => navigate('/app/leads')}
      />
    );
  }

  const tabItems = [
    { id: 'overview', label: 'Overview' },
    { id: 'timeline', label: `Timeline (${timeline.length})` },
    { id: 'ai-intel', label: 'AI Intelligence' },
    { id: 'followups', label: `Follow-Ups (${followups.length})` },
  ];

  return (
    <div className="space-y-6">
      {/* Top Back Navigation */}
      <button
        onClick={() => navigate('/app/leads')}
        className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Back to Leads Directory
      </button>

      {/* Header Card */}
      <Card className="p-6 bg-white border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Customer & Lead Info */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                {lead.customer?.full_name || 'Lead Details'}
              </h1>
              <StatusBadge status={lead.status?.name || 'NEW'} />
              <PriorityBadge score={lead.priority_score} />
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600">
              {lead.customer?.company_name && (
                <span className="font-semibold text-slate-800">{lead.customer.company_name}</span>
              )}
              {lead.customer?.primary_email && <span>{lead.customer.primary_email}</span>}
              {lead.customer?.primary_phone && <span>{lead.customer.primary_phone}</span>}
              <span className="flex items-center gap-1">
                Source: <LeadSourceBadge source={lead.source} />
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => aiAnalyzeMutation.mutate()}
              isLoading={aiAnalyzeMutation.isPending}
            >
              <Sparkles className="w-4 h-4 mr-1.5 text-teal-600" /> Re-Analyze AI
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedStatusId(lead.status_id);
                setShowStatusModal(true);
              }}
            >
              Change Status
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedUserId(lead.assigned_to_user_id ?? '');
                setShowAssignModal(true);
              }}
            >
              <UserPlus className="w-4 h-4 mr-1.5" /> Reassign
            </Button>
            <Button variant="primary" size="sm" onClick={() => setShowFollowupModal(true)}>
              <Plus className="w-4 h-4 mr-1.5" /> Schedule Follow-Up
            </Button>
          </div>
        </div>
      </Card>

      {/* Main Tabs Navigation */}
      <Tabs tabs={tabItems} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Primary Intelligence */}
          <div className="lg:col-span-2 space-y-6">
            {/* Qualification & AI Summary */}
            <Card className="p-6 bg-white">
              <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-600" /> AI Lead Qualification Summary
              </h3>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-teal-50/50 p-4 rounded-lg border border-teal-100">
                {lead.ai_summary || lead.qualification_summary || 'No AI summary generated yet for this lead.'}
              </p>

              {/* Next Best Action Card */}
              {lead.next_best_action && (
                <div className="mt-4 p-4 rounded-lg bg-indigo-50/60 border border-indigo-100">
                  <span className="text-[11px] font-bold text-indigo-900 uppercase tracking-wider block mb-1">
                    Recommended Next Best Action
                  </span>
                  <p className="text-xs sm:text-sm font-semibold text-indigo-950">
                    {lead.next_best_action}
                  </p>
                  {lead.next_best_action_reason && (
                    <p className="text-xs text-indigo-700 mt-1">
                      Reason: {lead.next_best_action_reason}
                    </p>
                  )}
                </div>
              )}
            </Card>

            {/* Score Breakdown */}
            <ScoreBreakdownCard
              leadScore={lead.lead_score}
              priorityScore={lead.priority_score}
              followupRiskScore={lead.followup_risk_score ?? lead.followup_risk}
              purchaseIntent={lead.purchase_intent}
              scoreBreakdown={lead.score_breakdown}
            />

            {/* Notes & Requirements */}
            <Card className="p-6 bg-white">
              <h3 className="text-sm font-bold text-slate-900 mb-3">Lead Notes & Context</h3>
              <p className="text-xs sm:text-sm text-slate-600 whitespace-pre-wrap">
                {lead.notes || 'No notes added yet for this lead.'}
              </p>

              {/* Tags */}
              {lead.tags && lead.tags.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-2 flex-wrap">
                  <Tag className="w-4 h-4 text-slate-400" />
                  {lead.tags.map((t, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-xs font-medium">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right Column: Key Details Sidebar */}
          <div className="space-y-6">
            <Card className="p-6 bg-white space-y-4">
              <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">
                Lead Overview
              </h3>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 block">Product Interest</span>
                  <span className="font-semibold text-slate-800 text-sm">
                    {lead.product?.name || 'General Product Interest'}
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 block">Assigned Representative</span>
                  <span className="font-semibold text-slate-800">
                    {lead.assigned_user?.full_name || 'Unassigned'}
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 block">Purchase Intent</span>
                  <div className="mt-1">
                    <PurchaseIntentBadge intent={lead.purchase_intent} />
                  </div>
                </div>

                <div>
                  <span className="text-slate-400 block">Next Scheduled Follow-Up</span>
                  <span className="font-semibold text-slate-800">
                    {lead.next_followup_at ? formatDate(lead.next_followup_at) : 'None scheduled'}
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 block">Created At</span>
                  <span className="text-slate-700">{formatDateTime(lead.created_at)}</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Timeline */}
      {activeTab === 'timeline' && (
        <Card className="p-6 bg-white">
          <h3 className="text-sm font-bold text-slate-900 mb-4">Activity Timeline</h3>
          {timeline.length === 0 ? (
            <EmptyState title="No interactions logged" description="Interactions will appear here as activity occurs." />
          ) : (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {timeline.map((item) => (
                <div key={item.id} className="relative group">
                  <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-teal-600 border-2 border-white" />
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{item.interaction_type || item.type}</span>
                    <span className="text-[11px] text-slate-400">{formatDateTime(item.created_at)}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{item.content || item.summary || 'Interaction recorded'}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Tab 3: AI Intelligence */}
      {activeTab === 'ai-intel' && (
        <div className="space-y-6">
          <ScoreBreakdownCard
            leadScore={lead.lead_score}
            priorityScore={lead.priority_score}
            followupRiskScore={lead.followup_risk_score ?? lead.followup_risk}
            purchaseIntent={lead.purchase_intent}
            scoreBreakdown={lead.score_breakdown}
          />
          <Card className="p-6 bg-white">
            <h3 className="text-sm font-bold text-slate-900 mb-2">Detailed AI Rationale</h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {lead.ai_summary || 'No granular rationale provided.'}
            </p>
          </Card>
        </div>
      )}

      {/* Tab 4: Follow-ups */}
      {activeTab === 'followups' && (
        <Card className="p-6 bg-white space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Scheduled & Past Follow-Ups</h3>
            <Button size="sm" onClick={() => setShowFollowupModal(true)}>
              <Plus className="w-4 h-4 mr-1" /> New Follow-Up
            </Button>
          </div>

          {followups.length === 0 ? (
            <EmptyState title="No follow-ups" description="No follow-ups have been scheduled for this lead." />
          ) : (
            <div className="divide-y divide-slate-100">
              {followups.map((fu) => (
                <div key={fu.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900">{fu.followup_type}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                        {fu.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">{fu.notes || 'No details provided.'}</p>
                    <span className="text-[11px] text-slate-400">Scheduled: {formatDateTime(fu.scheduled_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Status Modal */}
      <Modal isOpen={showStatusModal} onClose={() => setShowStatusModal(false)} title="Update Lead Status">
        <div className="space-y-4">
          <Select
            label="Select New Status"
            value={selectedStatusId}
            onChange={(e) => setSelectedStatusId(e.target.value)}
            options={statuses.map((st) => ({ label: st.name, value: st.id }))}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowStatusModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!selectedStatusId}
              onClick={() => updateStatusMutation.mutate(selectedStatusId)}
              isLoading={updateStatusMutation.isPending}
            >
              Update Status
            </Button>
          </div>
        </div>
      </Modal>

      {/* Assign Modal */}
      <Modal isOpen={showAssignModal} onClose={() => setShowAssignModal(false)} title="Assign Sales Representative">
        <div className="space-y-4">
          <Select
            label="Select Team Member"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            options={[
              { label: 'Unassigned', value: '' },
              ...teamMembers.map((m) => ({
                label: `${m.full_name} (${m.role})`,
                value: m.id,
              })),
            ]}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowAssignModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() =>
                reassignMutation.mutate(
                  selectedUserId || null,
                )
              }
              isLoading={reassignMutation.isPending}
            >
              Confirm Assignment
            </Button>
          </div>
        </div>
      </Modal>

      {/* Followup Modal */}
      <Modal isOpen={showFollowupModal} onClose={() => setShowFollowupModal(false)} title="Schedule Follow-Up">
        <div className="space-y-4">
          <Select
            label="Follow-Up Channel / Type"
            value={followupType}
            onChange={(e) => setFollowupType(e.target.value as FollowUpType)}
            options={Object.values(FollowUpType).map((ft) => ({ label: ft, value: ft }))}
          />
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Date & Time</label>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Notes / Instructions</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Call to clarify pricing and product options..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowFollowupModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!scheduledAt}
              onClick={() => createFollowupMutation.mutate()}
              isLoading={createFollowupMutation.isPending}
            >
              Schedule Follow-Up
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
