import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import {
  Users,
  Inbox,
  Flame,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { dashboardApi } from '@/api/dashboard';
import { MetricCard } from '@/components/common/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PurchaseIntentBadge, LeadSourceBadge, FollowUpStatusBadge } from '@/components/common/StatusBadge';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { formatDateTime, getScoreColor } from '@/lib/utils';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: dashboard, isLoading, isError, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.getDashboard(),
    refetchInterval: 60000,
  });

  if (isLoading) {
    return <LoadingSpinner message="Fetching live operational dashboard metrics..." />;
  }

  if (isError || !dashboard) {
    return (
      <EmptyState
        title="Unable to load dashboard"
        description="Could not connect to the OmniLead backend API."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  const { metrics, priority_leads, upcoming_followups, recent_activity, source_breakdown, purchase_intent_breakdown } = dashboard;

  return (
    <div className="space-y-6">
      {/* Top Banner Alert if Overdue Follow-ups or Reviews pending */}
      {(metrics.overdue_followups > 0 || metrics.enquiries_needing_review > 0) && (
        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <div className="text-xs">
              <span className="font-bold">Attention Required:</span> You have{' '}
              <span className="font-bold text-amber-900">{metrics.overdue_followups} overdue follow-up(s)</span> and{' '}
              <span className="font-bold text-amber-900">{metrics.enquiries_needing_review} enquiry review(s)</span> pending.
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate('/app/followups')}>
              View Overdue
            </Button>
          </div>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Active Leads"
          value={metrics.active_leads}
          subtitle={`Total: ${metrics.total_leads}`}
          accentColor="teal"
          icon={<Users className="w-5 h-5" />}
        />
        <MetricCard
          title="High Priority"
          value={metrics.high_priority_leads}
          subtitle="Score >= 70"
          accentColor="rose"
          icon={<Flame className="w-5 h-5" />}
        />
        <MetricCard
          title="New Enquiries"
          value={metrics.new_enquiries}
          subtitle={`${metrics.enquiries_needing_review} need review`}
          accentColor="amber"
          icon={<Inbox className="w-5 h-5" />}
        />
        <MetricCard
          title="Conversion Rate"
          value={`${metrics.conversion_rate.toFixed(1)}%`}
          subtitle={`${metrics.converted_leads} closed won`}
          accentColor="emerald"
          icon={<TrendingUp className="w-5 h-5" />}
        />
      </div>

      {/* High Priority Leads Queue Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-4">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold text-slate-900">AI Priority Queue</CardTitle>
              <span className="px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 text-xs font-bold border border-teal-200">
                Top Actionable Leads
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Leads ordered by highest priority score and risk</p>
          </div>
          <Link to="/app/priority">
            <Button variant="ghost" size="sm" className="gap-1.5 text-teal-700">
              <span>View All Priority Queue</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          {priority_leads.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">No high-priority leads currently queued.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Customer / Company</th>
                    <th className="py-3 px-4">Source</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Intent</th>
                    <th className="py-3 px-4 text-center">Priority</th>
                    <th className="py-3 px-4 text-center">Risk</th>
                    <th className="py-3 px-4">Next Best Action</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {priority_leads.slice(0, 6).map((lead) => {
                    const pScore = getScoreColor(lead.priority_score);
                    const rScore = getScoreColor(lead.followup_risk_score);

                    return (
                      <tr key={lead.lead_id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3.5 px-4 font-semibold text-slate-900">
                          <div>{lead.customer_name || 'Anonymous Customer'}</div>
                          {lead.company_name && <div className="text-[11px] font-normal text-slate-500">{lead.company_name}</div>}
                        </td>
                        <td className="py-3.5 px-4">
                          <LeadSourceBadge source={lead.source} />
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-700">
                          <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">
                            {lead.status_name}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <PurchaseIntentBadge intent={lead.purchase_intent} />
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className={`px-2 py-0.5 rounded-full font-bold border ${pScore.bg} ${pScore.text} ${pScore.border}`}>
                            {lead.priority_score ?? 'N/A'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className={`px-2 py-0.5 rounded-full font-bold border ${rScore.bg} ${rScore.text} ${rScore.border}`}>
                            {lead.followup_risk_score ?? 'N/A'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 max-w-xs text-slate-600 truncate">
                          {lead.next_best_action || 'Review requirement'}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <Button size="sm" variant="outline" onClick={() => navigate(`/app/leads/${lead.lead_id}`)}>
                            View Lead
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grid for Distribution & Upcoming Followups */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Lead Distribution Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-bold text-slate-900">Purchase Intent & Channel Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Purchase Intent Distribution</h4>
              <div className="space-y-2">
                {purchase_intent_breakdown.map((item) => (
                  <div key={item.purchase_intent} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-slate-700">{item.purchase_intent.replace(/_/g, ' ')}</span>
                      <span className="text-slate-900 font-bold">{item.count} ({item.percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-teal-600 h-full rounded-full" style={{ width: `${item.percentage}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Acquisition Channel Share</h4>
              <div className="grid grid-cols-2 gap-2">
                {source_breakdown.map((s) => (
                  <div key={s.source} className="p-2.5 rounded border border-slate-100 bg-slate-50 flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-700">{s.source.replace(/_/g, ' ')}</span>
                    <span className="text-xs font-bold text-slate-900">{s.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Follow-ups */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-bold text-slate-900">Upcoming & Due Follow-Ups</CardTitle>
            <Link to="/app/followups">
              <Button variant="ghost" size="sm" className="text-xs text-teal-700">
                View Queue
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {upcoming_followups.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">No upcoming follow-ups scheduled.</div>
            ) : (
              upcoming_followups.slice(0, 5).map((f) => (
                <div key={f.followup_id} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-xs font-bold text-slate-900">{f.customer_name || 'Customer'}</div>
                    <div className="text-[11px] text-slate-500 flex items-center gap-2">
                      <span>Type: {f.followup_type}</span>
                      <span>•</span>
                      <span>Scheduled: {formatDateTime(f.scheduled_at)}</span>
                    </div>
                  </div>
                  <FollowUpStatusBadge status={f.status} />
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent CRM Activity Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-bold text-slate-900">Recent Customer Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recent_activity.slice(0, 5).map((act) => (
              <div key={act.interaction_id} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-white">
                <div className="p-2 rounded-full bg-slate-100 text-slate-600 shrink-0">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{act.customer_name || 'Customer'}</span>
                    <span className="text-[10px] text-slate-400">{formatDateTime(act.occurred_at)}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5 truncate">{act.content || act.interaction_type}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
