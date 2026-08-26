import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { Calendar, RefreshCw } from 'lucide-react';
import { analyticsApi } from '@/api/analytics';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';

const COLORS = ['#0D9488', '#4F46E5', '#F59E0B', '#10B981', '#EF4444', '#6366F1', '#8B5CF6'];

export const AnalyticsPage: React.FC = () => {
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);

  const { data: analytics, isLoading, isError, refetch } = useQuery({
    queryKey: ['analytics', startDate, endDate],
    queryFn: () => analyticsApi.getAnalytics(startDate, endDate),
  });

  if (isLoading) {
    return <LoadingSpinner message="Generating real-time performance reports..." />;
  }

  if (isError || !analytics) {
    return (
      <EmptyState
        title="Unable to load analytics"
        description="Could not aggregate reporting metrics from backend."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  const { overview, conversion, trend, source_performance, team_performance, ai_metrics } = analytics;

  const sourceData = (source_performance || []).map((item) => ({
    name: item.source.replace(/_/g, ' '),
    leads: item.leads || 0,
    conversions: item.converted_leads || 0,
    enquiries: item.enquiries || 0,
  }));

  const trendData = (trend || []).map((item) => ({
    period: new Date(item.period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    enquiries: item.enquiries,
    leads: item.leads,
    conversions: item.converted_leads,
    followups: item.completed_followups,
  }));

  const aiReviewData = [
    { name: 'Accepted', value: ai_metrics?.accepted_reviews || 0 },
    { name: 'Edited', value: ai_metrics?.edited_reviews || 0 },
    { name: 'Rejected', value: ai_metrics?.rejected_reviews || 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Header & Date Range selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Analytics & Performance Reports</h2>
          <p className="text-xs text-slate-500 mt-1">
            Conversion pipelines, acquisition channels, team output, and AI quality metrics.
          </p>
        </div>

        <div className="flex items-center gap-3 bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
          <Calendar className="w-4 h-4 text-slate-400 ml-1" />
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="text-xs border-0 bg-transparent text-slate-800 font-medium focus:ring-0"
          />
          <span className="text-slate-400 text-xs">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="text-xs border-0 bg-transparent text-slate-800 font-medium focus:ring-0"
          />
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-white border border-slate-200">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Total Leads</span>
          <span className="text-2xl font-bold text-slate-900 mt-1 block">{overview?.total_leads || 0}</span>
        </Card>

        <Card className="p-4 bg-white border border-slate-200">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Converted Leads</span>
          <span className="text-2xl font-bold text-emerald-600 mt-1 block">{conversion?.converted_leads || 0}</span>
        </Card>

        <Card className="p-4 bg-white border border-slate-200">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Conversion Rate</span>
          <span className="text-2xl font-bold text-teal-600 mt-1 block">
            {overview?.conversion_rate != null ? `${overview.conversion_rate.toFixed(1)}%` : '0%'}
          </span>
        </Card>

        <Card className="p-4 bg-white border border-slate-200">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Avg Lead Score</span>
          <span className="text-2xl font-bold text-indigo-600 mt-1 block">
            {overview?.average_lead_score != null ? Math.round(overview.average_lead_score) : 0}
          </span>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Trends */}
        <Card className="p-6 bg-white border border-slate-200">
          <h3 className="text-sm font-bold text-slate-900 mb-4">Lead & Conversion Trends</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="period" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip />
                <Line type="monotone" dataKey="leads" stroke="#0D9488" strokeWidth={2} name="Leads" />
                <Line type="monotone" dataKey="conversions" stroke="#10B981" strokeWidth={2} name="Conversions" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Source Performance */}
        <Card className="p-6 bg-white border border-slate-200">
          <h3 className="text-sm font-bold text-slate-900 mb-4">Performance by Acquisition Channel</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sourceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="name" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip />
                <Bar dataKey="leads" fill="#0D9488" radius={[4, 4, 0, 0]} name="Leads" />
                <Bar dataKey="conversions" fill="#10B981" radius={[4, 4, 0, 0]} name="Converted" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Team & AI Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Review Distribution */}
        <Card className="p-6 bg-white border border-slate-200">
          <h3 className="text-sm font-bold text-slate-900 mb-4">AI Human Review Accuracy</h3>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={aiReviewData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {aiReviewData.map((_, index) => (
                    <Cell key={`ai-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs mt-2">
            {aiReviewData.map((entry, idx) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                <span className="text-slate-600 font-medium">{entry.name}: {entry.value}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Team Performance Table */}
        <Card className="p-6 bg-white border border-slate-200 lg:col-span-2">
          <h3 className="text-sm font-bold text-slate-900 mb-4">Team Performance</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2">Salesperson</th>
                  <th className="px-3 py-2">Assigned</th>
                  <th className="px-3 py-2">Active</th>
                  <th className="px-3 py-2">Converted</th>
                  <th className="px-3 py-2">Conv %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(team_performance || []).length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-center text-slate-400">
                      No team metric data recorded for this timeframe.
                    </td>
                  </tr>
                ) : (
                  (team_performance || []).map((member) => (
                    <tr key={member.user_id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-medium text-slate-900">{member.full_name}</td>
                      <td className="px-3 py-2">{member.assigned_leads}</td>
                      <td className="px-3 py-2">{member.active_leads}</td>
                      <td className="px-3 py-2 text-emerald-600 font-semibold">{member.converted_leads}</td>
                      <td className="px-3 py-2 font-semibold text-slate-900">{member.conversion_rate.toFixed(1)}%</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
};
