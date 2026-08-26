import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Clock, RefreshCw } from 'lucide-react';
import { followupsApi } from '@/api/followups';
import { FollowUpStatus } from '@/types/api';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Tabs } from '@/components/ui/Tabs';
import { Modal } from '@/components/ui/Modal';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { FollowUpStatusBadge } from '@/components/common/StatusBadge';
import { formatDateTime } from '@/lib/utils';

export const FollowupsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState('assigned-to-me');
  const [rescheduleId, setRescheduleId] = useState<string | null>(null);
  const [rescheduleDate, setRescheduleDate] = useState('');
  const [rescheduleNotes, setRescheduleNotes] = useState<string | null>(null);

  const nowISO = new Date().toISOString();

  // Queries
  const { data: myFollowups = [], isLoading: loadingMy, refetch: refetchMy } = useQuery({
    queryKey: ['followups-me'],
    queryFn: () => followupsApi.assignedToMe(),
    enabled: activeTab === 'assigned-to-me',
  });

  const { data: overdueFollowups = [], isLoading: loadingOverdue, refetch: refetchOverdue } = useQuery({
    queryKey: ['followups-overdue'],
    queryFn: () => followupsApi.listOverdue(nowISO),
    enabled: activeTab === 'overdue',
  });

  const { data: allFollowups = [], isLoading: loadingAll, refetch: refetchAll } = useQuery({
    queryKey: ['followups-all'],
    queryFn: () => followupsApi.list(),
    enabled: activeTab === 'all',
  });

  // Complete Mutation
  const completeMutation = useMutation({
    mutationFn: (followupId: string) =>
      followupsApi.complete(followupId, {
        completed_at: new Date().toISOString(),
        outcome: 'Completed',
      }),
    onSuccess: () => {
      success('Follow-Up Completed', 'Status updated to COMPLETED.');
      queryClient.invalidateQueries({ queryKey: ['followups-me'] });
      queryClient.invalidateQueries({ queryKey: ['followups-overdue'] });
      queryClient.invalidateQueries({ queryKey: ['followups-all'] });
    },
    onError: (err: any) => {
      error('Failed', err.message || 'Could not complete follow-up.');
    },
  });

  // Cancel Mutation
  const cancelMutation = useMutation({
    mutationFn: (followupId: string) => followupsApi.cancel(followupId),
    onSuccess: () => {
      success('Follow-Up Cancelled', 'Status updated to CANCELLED.');
      queryClient.invalidateQueries({ queryKey: ['followups-me'] });
      queryClient.invalidateQueries({ queryKey: ['followups-overdue'] });
      queryClient.invalidateQueries({ queryKey: ['followups-all'] });
    },
    onError: (err: any) => {
      error('Failed', err.message || 'Could not cancel follow-up.');
    },
  });

  // Reschedule Mutation
  const rescheduleMutation = useMutation({
    mutationFn: () =>
      followupsApi.reschedule(rescheduleId!, {
        scheduled_at: new Date(rescheduleDate).toISOString(),
        notes: rescheduleNotes,
      }),
    onSuccess: () => {
      success('Follow-Up Rescheduled', 'New target date set.');
      setRescheduleId(null);
      setRescheduleDate('');
      setRescheduleNotes(null);
      queryClient.invalidateQueries({ queryKey: ['followups-me'] });
      queryClient.invalidateQueries({ queryKey: ['followups-overdue'] });
      queryClient.invalidateQueries({ queryKey: ['followups-all'] });
    },
    onError: (err: any) => {
      error('Failed', err.message || 'Could not reschedule.');
    },
  });

  const tabItems = [
    { id: 'assigned-to-me', label: 'Assigned to Me' },
    { id: 'overdue', label: 'Overdue' },
    { id: 'all', label: 'All Follow-Ups' },
  ];

  const currentList =
    activeTab === 'assigned-to-me' ? myFollowups : activeTab === 'overdue' ? overdueFollowups : allFollowups;
  const isLoading = loadingMy || loadingOverdue || loadingAll;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Follow-Ups Management</h2>
          <p className="text-xs text-slate-500 mt-1">
            Track, complete, and reschedule sales touchpoints across all leads.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => {
          refetchMy();
          refetchOverdue();
          refetchAll();
        }}>
          <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh List
        </Button>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabItems} activeTab={activeTab} onChange={setActiveTab} />

      {/* Followup List */}
      {isLoading ? (
        <LoadingSpinner message="Fetching scheduled follow-ups..." />
      ) : currentList.length === 0 ? (
        <EmptyState title="No follow-ups found" description="There are no follow-ups scheduled in this view." />
      ) : (
        <div className="space-y-4">
          {currentList.map((fu) => (
            <Card key={fu.id} className="p-5 bg-white border border-slate-200 hover:border-slate-300 transition-all">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-teal-50 text-teal-800 border border-teal-200">
                      {fu.followup_type}
                    </span>
                    <FollowUpStatusBadge status={fu.status} />
                    {fu.lead_id && (
                      <button
                        onClick={() => navigate(`/app/leads/${fu.lead_id}`)}
                        className="text-xs font-semibold text-teal-700 hover:underline"
                      >
                        View Lead &rarr;
                      </button>
                    )}
                  </div>

                  <p className="text-xs text-slate-700 font-medium mt-1">
                    {fu.notes || 'No detailed instructions provided.'}
                  </p>

                  <div className="flex items-center gap-4 text-[11px] text-slate-400 mt-2">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" /> Scheduled: {formatDateTime(fu.scheduled_at)}
                    </span>
                    {fu.completed_at && (
                      <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Completed: {formatDateTime(fu.completed_at)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                {fu.status !== FollowUpStatus.COMPLETED && fu.status !== FollowUpStatus.CANCELLED && (
                  <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                    {fu.status === FollowUpStatus.SCHEDULED && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setRescheduleId(fu.id);
                          setRescheduleDate('');
                          setRescheduleNotes(fu.notes ?? null);
                        }}
                      >
                        Reschedule
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => cancelMutation.mutate(fu.id)}
                      className="text-rose-600 hover:bg-rose-50 border-rose-200"
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => completeMutation.mutate(fu.id)}
                      isLoading={completeMutation.isPending}
                    >
                      <CheckCircle2 className="w-4 h-4 mr-1" /> Mark Complete
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Reschedule Modal */}
      <Modal
        isOpen={!!rescheduleId}
        onClose={() => {
          setRescheduleId(null);
          setRescheduleDate('');
          setRescheduleNotes(null);
        }}
        title="Reschedule Follow-Up"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">New Target Date & Time</label>
            <input
              type="datetime-local"
              value={rescheduleDate}
              onChange={(e) => setRescheduleDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => {
                setRescheduleId(null);
                setRescheduleDate('');
                setRescheduleNotes(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!rescheduleDate}
              onClick={() => rescheduleMutation.mutate()}
              isLoading={rescheduleMutation.isPending}
            >
              Confirm Reschedule
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
