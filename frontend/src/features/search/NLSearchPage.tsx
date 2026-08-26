import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, Sparkles, ArrowRight } from 'lucide-react';
import { searchApi } from '@/api/search';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { PriorityBadge, StatusBadge, PurchaseIntentBadge } from '@/components/common/StatusBadge';

export const NLSearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryParam = searchParams.get('q') || '';

  const [inputQuery, setInputQuery] = useState(queryParam);

  useEffect(() => {
    setInputQuery(queryParam);
  }, [queryParam]);

  const { data: searchResults, isLoading, isError, refetch } = useQuery({
    queryKey: ['nl-search', queryParam],
    queryFn: () => searchApi.naturalLanguageSearch(queryParam),
    enabled: !!queryParam.trim(),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputQuery.trim()) {
      setSearchParams({ q: inputQuery.trim() });
    }
  };

  const leads = searchResults?.results ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Natural-Language Search</h2>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-teal-100 text-teal-800">
            Powered by Gemini
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Search leads, conversations, and customer intents using plain conversational English.
        </p>
      </div>

      {/* Query Bar */}
      <Card className="p-4 bg-white">
        <form onSubmit={handleSearch} className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="e.g. 'Show me high intent WhatsApp leads interested in enterprise software with high priority'"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>
          <Button type="submit" variant="primary" size="sm">
            <Sparkles className="w-4 h-4 mr-1.5" /> Execute Search
          </Button>
        </form>
      </Card>

      {/* Applied Parsed Filter Summary */}
      {searchResults?.filters && (
        <Card className="p-4 bg-teal-50/50 border border-teal-100">
          <span className="text-xs font-bold text-teal-900 block mb-1">
            AI Query Understanding & Applied Filters:
          </span>
          <div className="text-xs text-teal-800 font-mono bg-white/80 p-2.5 rounded border border-teal-200">
            {JSON.stringify(searchResults.filters, null, 2)}
          </div>
        </Card>
      )}

      {/* Results */}
      {!queryParam ? (
        <EmptyState
          title="Enter a natural-language search query"
          description="Try typing prompts like 'High priority leads from WhatsApp' or 'Overdue follow-up calls'."
        />
      ) : isLoading ? (
        <LoadingSpinner message="Parsing natural language query & querying vector index..." />
      ) : isError ? (
        <EmptyState
          title="Search Failed"
          description="Could not parse query."
          actionLabel="Retry"
          onAction={() => refetch()}
        />
      ) : leads.length === 0 ? (
        <EmptyState title="No matching leads found" description="Try broadening your search query." />
      ) : (
        <div className="space-y-4">
          {leads.map((lead) => (
            <Card
              key={lead.lead_id}
              className="p-5 bg-white border border-slate-200 hover:border-slate-300 transition-all cursor-pointer"
              onClick={() => navigate(`/app/leads/${lead.lead_id}`)}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">
                      {lead.customer_name || lead.company_name || 'Matched Lead'}
                    </h3>
                    <StatusBadge status={lead.status_name} />
                    <PriorityBadge score={lead.priority_score} />
                    <PurchaseIntentBadge intent={lead.purchase_intent} />
                  </div>

                  <p className="text-xs text-slate-600 mt-1">
                    {lead.qualification_summary || lead.conversation_summary || lead.requirement || 'No summary available.'}
                  </p>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/app/leads/${lead.lead_id}`);
                  }}
                  className="text-teal-700 hover:text-teal-800 shrink-0 self-end md:self-center"
                >
                  View Lead <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
