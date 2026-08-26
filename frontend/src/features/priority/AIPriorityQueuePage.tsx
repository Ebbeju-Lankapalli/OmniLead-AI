import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles, RefreshCw } from 'lucide-react';
import { leadsApi } from '@/api/leads';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import {
  StatusBadge,
  LeadSourceBadge,
  PurchaseIntentBadge,
  PriorityBadge,
} from '@/components/common/StatusBadge';
import { getScoreColor } from '@/lib/utils';

export const AIPriorityQueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [minPriority, setMinPriority] = useState<number>(0);

  const { data: queue = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['priority-queue', minPriority],
    queryFn: () => leadsApi.getPriorityQueue(minPriority),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return <LoadingSpinner message="Evaluating AI priority scores & urgent actions..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Unable to load AI priority queue"
        description="Could not connect to the OmniLead backend AI service."
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
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Priority Queue</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-teal-100 text-teal-800">
              Ranked by Urgency
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time AI ranking based on purchase intent, deal value, engagement, and follow-up risk.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Priority Threshold Filter */}
          <select
            value={minPriority}
            onChange={(e) => setMinPriority(Number(e.target.value))}
            className="px-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value={0}>All Priorities (&ge; 0)</option>
            <option value={50}>Medium+ (&ge; 50)</option>
            <option value={75}>High Priority Only (&ge; 75)</option>
          </select>

          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh Queue
          </Button>
        </div>
      </div>

      {/* Queue List */}
      {queue.length === 0 ? (
        <EmptyState
          title="Priority Queue Empty"
          description="No leads match the requested priority threshold."
          actionLabel="Show All Leads"
          onAction={() => setMinPriority(0)}
        />
      ) : (
        <div className="space-y-4">
          {queue.map((lead, index) => {
            const priorityScore = lead.priority_score || 0;
            const isHighUrgency = priorityScore >= 75;
            const followupRisk = lead.followup_risk || lead.followup_risk_score || 0;

            return (
              <Card
                key={lead.id}
                className={`p-5 bg-white border transition-all hover:shadow-md cursor-pointer ${
                  isHighUrgency ? 'border-amber-200 ring-1 ring-amber-200/50' : 'border-slate-200'
                }`}
                onClick={() => navigate(`/app/leads/${lead.id}`)}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Rank & Customer Details */}
                  <div className="flex items-start gap-4">
                    <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center font-extrabold text-sm text-slate-700 shrink-0 border border-slate-200">
                      #{index + 1}
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900">
                          {lead.customer?.full_name || 'Unassigned Lead'}
                        </h3>
                        <StatusBadge status={lead.status?.name || 'NEW'} />
                        <PriorityBadge score={lead.priority_score} />
                        <PurchaseIntentBadge intent={lead.purchase_intent} />
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        {lead.customer?.company_name && (
                          <span className="font-semibold text-slate-700">{lead.customer.company_name}</span>
                        )}
                        <span>Product: <strong className="text-slate-700">{lead.product?.name || 'General'}</strong></span>
                        <span>Source: <LeadSourceBadge source={lead.source} /></span>
                        {lead.assigned_user && <span>Assigned: <strong className="text-slate-700">{lead.assigned_user.full_name}</strong></span>}
                      </div>
                    </div>
                  </div>

                  {/* Score Badges */}
                  <div className="flex items-center gap-4 bg-slate-50 p-3 rounded-lg border border-slate-100 shrink-0">
                    <div className="text-center">
                      <span className="text-[10px] text-slate-400 font-medium uppercase block">Lead Score</span>
                      <span className={`text-sm font-extrabold ${getScoreColor(lead.lead_score)}`}>
                        {lead.lead_score != null ? Math.round(lead.lead_score) : 0}
                      </span>
                    </div>
                    <div className="h-6 w-px bg-slate-200" />
                    <div className="text-center">
                      <span className="text-[10px] text-slate-400 font-medium uppercase block">Follow-up Risk</span>
                      <span className={`text-sm font-extrabold ${followupRisk > 50 ? 'text-rose-600' : 'text-slate-700'}`}>
                        {Math.round(followupRisk)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Next Best Action Banner */}
                {lead.next_best_action && (
                  <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-xs">
                      <Sparkles className="w-4 h-4 text-teal-600 shrink-0" />
                      <span className="font-bold text-slate-900">Next Action:</span>
                      <span className="text-slate-700">{lead.next_best_action}</span>
                      {lead.next_best_action_reason && (
                        <span className="text-slate-400 italic">({lead.next_best_action_reason})</span>
                      )}
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/app/leads/${lead.id}`);
                      }}
                      className="text-teal-700 hover:text-teal-800 self-end sm:self-auto"
                    >
                      View & Execute <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
