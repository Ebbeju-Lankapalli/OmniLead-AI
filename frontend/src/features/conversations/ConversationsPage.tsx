import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Sparkles, RefreshCw } from 'lucide-react';
import { conversationsApi } from '@/api/conversations';
import { customersApi } from '@/api/customers';
import { aiApi } from '@/api/ai';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { formatDateTime } from '@/lib/utils';

export const ConversationsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [filterOpen, setFilterOpen] = useState<boolean | undefined>(undefined);

  const { data: conversations = [], isLoading, refetch } = useQuery({
    queryKey: ['conversations', filterOpen],
    queryFn: () => conversationsApi.list({ open_only: filterOpen }),
  });

  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customersApi.list(),
  });

  const customerMap = React.useMemo(() => {
    const map = new Map<string, string>();
    customers.forEach((c) => {
      map.set(c.id, c.full_name || c.company_name || c.primary_phone || c.primary_email || 'Customer');
    });
    return map;
  }, [customers]);

  // AI Analyze Conversation Mutation
  const aiAnalyzeMutation = useMutation({
    mutationFn: (conversationId: string) => aiApi.analyzeConversation(conversationId, true),
    onSuccess: () => {
      success('AI Analysis Completed', 'Conversation summary and intent extracted.');
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    onError: (err: any) => {
      error('Analysis Failed', err.message || 'Could not analyze conversation.');
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Conversations & Thread History</h2>
          <p className="text-xs text-slate-500 mt-1">
            Omnichannel thread logs across WhatsApp, Instagram, and Voice calls.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh Threads
        </Button>
      </div>

      {/* Filter Bar */}
      <Card className="p-4 bg-white">
        <div className="flex items-center gap-3">
          <select
            value={filterOpen === undefined ? 'all' : filterOpen ? 'open' : 'closed'}
            onChange={(e) => {
              const val = e.target.value;
              setFilterOpen(val === 'all' ? undefined : val === 'open');
            }}
            className="w-48 px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value="all">All Conversations</option>
            <option value="open">Open Threads Only</option>
            <option value="closed">Closed Threads Only</option>
          </select>
        </div>
      </Card>

      {/* List */}
      {isLoading ? (
        <LoadingSpinner message="Fetching message threads..." />
      ) : conversations.length === 0 ? (
        <EmptyState title="No conversation records" description="No thread logs available." />
      ) : (
        <div className="space-y-4">
          {conversations.map((conv) => {
            const isClosed = Boolean(conv.closed_at) || conv.status === 'closed';
            const customerName = customerMap.get(conv.customer_id) || 'Customer';
            return (
              <Card key={conv.id} className="p-5 bg-white border border-slate-200 hover:border-slate-300 transition-all">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-800 border border-slate-200">
                        {conv.channel}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">
                        {customerName}
                      </h3>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          isClosed ? 'bg-slate-100 text-slate-600' : 'bg-emerald-50 text-emerald-800'
                        }`}
                      >
                        {isClosed ? 'Closed' : 'Active'}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 mt-2 bg-slate-50 p-3 rounded-md border border-slate-100">
                      {conv.summary || 'No conversation summary generated yet.'}
                    </p>

                    <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 mt-2">
                      <span>Started: {formatDateTime(conv.created_at)}</span>
                      {conv.lead_id && (
                        <button
                          onClick={() => navigate(`/app/leads/${conv.lead_id}`)}
                          className="text-teal-700 font-semibold hover:underline"
                        >
                          Linked Lead &rarr;
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => aiAnalyzeMutation.mutate(conv.id)}
                      isLoading={aiAnalyzeMutation.isPending}
                    >
                      <Sparkles className="w-4 h-4 mr-1 text-teal-600" /> AI Analyze
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
