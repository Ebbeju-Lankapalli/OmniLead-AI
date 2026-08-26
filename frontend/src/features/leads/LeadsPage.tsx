import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import { Search, Plus, RefreshCw } from 'lucide-react';
import { leadsApi } from '@/api/leads';
import { LeadSource, PurchaseIntent } from '@/types/api';
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
import { formatDate } from '@/lib/utils';

export const LeadsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedIntent, setSelectedIntent] = useState<string>('');

  const { data: leads = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['leads', selectedStatus],
    queryFn: () => leadsApi.list({ status_id: selectedStatus || undefined }),
  });

  const { data: statuses = [] } = useQuery({
    queryKey: ['lead-statuses'],
    queryFn: () => leadsApi.listStatuses(),
  });

  // Client-side filtering for search term, source, and intent
  const filteredLeads = leads.filter((lead) => {
    const matchesSearch =
      !searchTerm ||
      lead.customer?.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.customer?.company_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.customer?.primary_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.product?.name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSource = !selectedSource || lead.source === selectedSource;
    const matchesIntent = !selectedIntent || lead.purchase_intent === selectedIntent;

    return matchesSearch && matchesSource && matchesIntent;
  });

  if (isLoading) {
    return <LoadingSpinner message="Fetching sales leads directory..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Unable to load leads"
        description="Could not connect to the OmniLead backend API."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Sales Leads Directory</h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage, qualify, and track lead conversion pipelines.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh
          </Button>
          <Link to="/app/leads/new">
            <Button variant="primary" size="sm">
              <Plus className="w-4 h-4 mr-1.5" /> Create Lead
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-white">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by customer name, company, email, or product..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:bg-white"
            />
          </div>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full md:w-44 px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value="">All Statuses</option>
            {statuses.map((st) => (
              <option key={st.id} value={st.id}>
                {st.name}
              </option>
            ))}
          </select>

          {/* Channel Source Filter */}
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="w-full md:w-44 px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value="">All Sources</option>
            {Object.values(LeadSource).map((src) => (
              <option key={src} value={src}>
                {src}
              </option>
            ))}
          </select>

          {/* Purchase Intent Filter */}
          <select
            value={selectedIntent}
            onChange={(e) => setSelectedIntent(e.target.value)}
            className="w-full md:w-44 px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value="">All Intents</option>
            {Object.values(PurchaseIntent).map((pi) => (
              <option key={pi} value={pi}>
                {pi.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Leads Table */}
      <Card className="overflow-hidden bg-white">
        {filteredLeads.length === 0 ? (
          <EmptyState
            title="No leads found"
            description={
              searchTerm || selectedStatus || selectedSource || selectedIntent
                ? 'No leads match the selected filter criteria.'
                : 'Get started by creating your first sales lead.'
            }
            actionLabel="Add Lead"
            onAction={() => navigate('/app/leads/new')}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Product</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Source</th>
                  <th className="py-3 px-4">Intent</th>
                  <th className="py-3 px-4 text-center">Score</th>
                  <th className="py-3 px-4 text-center">Priority</th>
                  <th className="py-3 px-4">Assigned To</th>
                  <th className="py-3 px-4">Next Follow-Up</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs sm:text-sm text-slate-700">
                {filteredLeads.map((lead) => (
                  <tr
                    key={lead.id}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                    onClick={() => navigate(`/app/leads/${lead.id}`)}
                  >
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      <div>{lead.customer?.full_name || 'Unassigned Customer'}</div>
                      <div className="text-[11px] text-slate-400 font-normal">
                        {lead.customer?.company_name || lead.customer?.primary_email || lead.customer?.primary_phone}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-700">
                      {lead.product?.name || <span className="text-slate-400">—</span>}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={lead.status?.name || 'NEW'} />
                    </td>
                    <td className="py-3.5 px-4">
                      <LeadSourceBadge source={lead.source} />
                    </td>
                    <td className="py-3.5 px-4">
                      <PurchaseIntentBadge intent={lead.purchase_intent} />
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 font-bold text-slate-800 text-xs">
                        {lead.lead_score != null ? Math.round(lead.lead_score) : 0}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <PriorityBadge score={lead.priority_score} />
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {lead.assigned_user?.full_name || (
                        <span className="text-slate-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {lead.next_followup_at ? (
                        formatDate(lead.next_followup_at)
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/app/leads/${lead.id}`)}
                        className="text-teal-700 hover:text-teal-800"
                      >
                        View Details
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
