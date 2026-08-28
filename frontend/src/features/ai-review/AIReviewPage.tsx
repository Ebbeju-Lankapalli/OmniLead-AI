import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Edit3, XCircle, RefreshCw, AlertTriangle } from 'lucide-react';
import { aiApi } from '@/api/ai';
import { AIReviewDecision } from '@/types/api';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';

export const AIReviewPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error } = useToast();
  const { user } = useAuth();

  const [page] = useState(1);
  const [includeReviewed, setIncludeReviewed] = useState(false);

  // Edit Feedback Modal State
  const [editAnalysisId, setEditAnalysisId] = useState<string | null>(null);
  const [originalResult, setOriginalResult] = useState<Record<string, any>>({});
  const [correctedText, setCorrectedText] = useState('');
  const [feedbackNotes, setFeedbackNotes] = useState('');

  const { data: reviewQueue, isLoading, isError, refetch } = useQuery({
    queryKey: ['ai-review-queue', page, includeReviewed],
    queryFn: () => aiApi.getReviewQueue(page, 20, includeReviewed),
  });

  // Submit Feedback Mutation
  const feedbackMutation = useMutation({
    mutationFn: ({
      analysisId,
      decision,
      origResult,
      finalResult,
      changedFields,
      notes,
    }: {
      analysisId: string;
      decision: AIReviewDecision;
      origResult: Record<string, any>;
      finalResult?: Record<string, any> | null;
      changedFields?: string[];
      notes?: string;
    }) => {
      if (!user) {
        throw new Error('Authenticated user is required to submit AI feedback.');
      }

      return aiApi.submitFeedback(analysisId, {
        organization_id: user.organization_id,
        ai_analysis_id: analysisId,
        reviewed_by_user_id: user.id,
        decision,
        original_result: origResult,
        final_result: finalResult,
        changed_fields: changedFields,
        feedback_notes: notes,
      });
    },
    onSuccess: () => {
      success('Feedback Submitted', 'AI review recorded and model guardrails updated.');
      setEditAnalysisId(null);
      setOriginalResult({});
      setCorrectedText('');
      setFeedbackNotes('');
      queryClient.invalidateQueries({ queryKey: ['ai-review-queue'] });
    },
    onError: (err: any) => {
      error('Submission Failed', err.message || 'Could not record feedback.');
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading AI human-in-the-loop review queue..." />;
  }

  if (isError || !reviewQueue) {
    return (
      <EmptyState
        title="Unable to load AI review queue"
        description="Could not connect to the backend review service."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  const items = reviewQueue.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Human-in-the-Loop Review Queue</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800">
              Low Confidence & Flags
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Review and validate AI extracted intents, scores, and classifications before final action execution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <input
              type="checkbox"
              checked={includeReviewed}
              onChange={(e) => setIncludeReviewed(e.target.checked)}
              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
            />
            Include Reviewed Items
          </label>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh Queue
          </Button>
        </div>
      </div>

      {/* List */}
      {items.length === 0 ? (
        <EmptyState
          title="All AI outputs verified"
          description="There are currently no AI analyses awaiting human review."
        />
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <Card key={item.analysis.id} className="p-5 bg-white border border-slate-200 hover:border-slate-300 transition-all">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-indigo-50 text-indigo-800 border border-indigo-200">
                      {item.analysis.analysis_type}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
                      Confidence: {item.analysis.model_confidence != null ? (item.analysis.model_confidence * 100).toFixed(0) : 'N/A'}%
                    </span>
                    {item.requires_review && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-50 text-rose-800 border border-rose-200">
                        Needs Review
                      </span>
                    )}
                  </div>

                  {item.review_reason && (
                    <div className="p-2.5 rounded bg-amber-50/60 border border-amber-200/60 text-amber-900 text-xs flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      <span>Review Reason: <strong>{item.review_reason}</strong></span>
                    </div>
                  )}

                  {/* AI Output Content preview */}
                  <div className="bg-slate-50 p-3 rounded-md border border-slate-200 text-xs text-slate-800 font-mono overflow-x-auto max-h-40">
                    {JSON.stringify(item.result, null, 2)}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0 self-end lg:self-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      feedbackMutation.mutate({
                        analysisId: item.analysis.id,
                        decision: AIReviewDecision.REJECTED,
                        origResult: item.result || {},
                      });
                    }}
                    className="text-rose-600 border-rose-200 hover:bg-rose-50"
                  >
                    <XCircle className="w-4 h-4 mr-1" /> Reject
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditAnalysisId(item.analysis.id);
                      setOriginalResult(item.result || {});
                      setCorrectedText(JSON.stringify(item.result, null, 2));
                    }}
                  >
                    <Edit3 className="w-4 h-4 mr-1 text-slate-600" /> Edit & Accept
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      feedbackMutation.mutate({
                        analysisId: item.analysis.id,
                        decision: AIReviewDecision.ACCEPTED,
                        origResult: item.result || {},
                        finalResult: item.result || {},
                      });
                    }}
                    isLoading={feedbackMutation.isPending}
                  >
                    <CheckCircle2 className="w-4 h-4 mr-1" /> Accept AI Result
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Feedback Modal */}
      <Modal isOpen={!!editAnalysisId} onClose={() => setEditAnalysisId(null)} title="Edit AI Result & Submit Feedback">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Corrected Output (JSON or Text)</label>
            <textarea
              rows={6}
              value={correctedText}
              onChange={(e) => setCorrectedText(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 text-slate-100 font-mono border border-slate-700 rounded-md text-xs focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Feedback Notes / Explanation</label>
            <input
              type="text"
              placeholder="e.g. Corrected purchase intent from General to High Intent..."
              value={feedbackNotes}
              onChange={(e) => setFeedbackNotes(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setEditAnalysisId(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                let parsed: any = correctedText;
                try {
                  parsed = JSON.parse(correctedText);
                } catch {
                  // Keep as string if not valid json
                }
                if (editAnalysisId) {
                  feedbackMutation.mutate({
                    analysisId: editAnalysisId,
                    decision: AIReviewDecision.EDITED,
                    origResult: originalResult,
                    finalResult:
  typeof parsed === 'object' && parsed !== null
    ? parsed
    : { corrected_text: parsed },
changedFields:
  typeof parsed === 'object' && parsed !== null
    ? Object.keys(parsed).filter(
        (key) =>
          JSON.stringify(originalResult[key]) !==
          JSON.stringify(parsed[key])
      )
    : ['corrected_text'],
                    notes: feedbackNotes,
                  });
                }
              }}
              isLoading={feedbackMutation.isPending}
            >
              Submit Corrected Result
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
