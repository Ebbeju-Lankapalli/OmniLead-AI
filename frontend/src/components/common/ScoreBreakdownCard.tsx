import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Sparkles, Info } from 'lucide-react';
import { getScoreColor } from '@/lib/utils';

export interface ScoreBreakdownProps {
  leadScore?: number | null;
  priorityScore?: number | null;
  followupRiskScore?: number | null;
  followupRisk?: number | null;
  purchaseIntent?: any;
  scoreBreakdown?: Record<string, any>;
  nextBestAction?: string | null;
  nextBestActionReason?: string | null;
  qualificationSummary?: string | null;
}

const formatLabel = (key: string): string =>
  key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const formatValue = (value: any): string => {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  return String(value);
};

const isNumericValue = (value: any): boolean =>
  typeof value === 'number' ||
  (typeof value === 'string' && value.trim() !== '' && !Number.isNaN(Number(value)));

export const ScoreBreakdownCard: React.FC<ScoreBreakdownProps> = ({
  leadScore,
  priorityScore,
  followupRiskScore,
  followupRisk,
  scoreBreakdown = {},
  nextBestAction,
  nextBestActionReason,
  qualificationSummary,
}) => {
  const riskVal = followupRiskScore ?? followupRisk;
  const pScore = getScoreColor(priorityScore);

  return (
    <Card className="border-teal-100 bg-white">
      <CardHeader className="bg-slate-50/60 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-md bg-teal-50 text-teal-700">
              <Sparkles className="w-4 h-4" />
            </div>

            <CardTitle className="text-sm font-semibold text-slate-900">
              AI Priority & Intelligence Breakdown
            </CardTitle>
          </div>

          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${pScore.bg} ${pScore.text} ${pScore.border}`}
          >
            Priority Score: {priorityScore ?? 'N/A'}
          </span>
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-5">

        {/* Main Scores Grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-center">
            <span className="text-xs text-slate-500 font-medium">
              Lead Quality Score
            </span>
            <div className="text-lg font-bold text-slate-900 mt-0.5">
              {leadScore ?? 'N/A'} / 100
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-center">
            <span className="text-xs text-slate-500 font-medium">
              Priority Score
            </span>
            <div className="text-lg font-bold text-teal-700 mt-0.5">
              {priorityScore ?? 'N/A'} / 100
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-center">
            <span className="text-xs text-slate-500 font-medium">
              Follow-Up Risk
            </span>
            <div className="text-lg font-bold text-amber-700 mt-0.5">
              {riskVal != null ? Math.round(riskVal) : 'N/A'} / 100
            </div>
          </div>
        </div>

        {/* Explainability Breakdown Factors */}
        {Object.keys(scoreBreakdown).length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Scoring Factors & Contributions
            </h4>

            <div className="space-y-3">
              {Object.entries(scoreBreakdown).map(([key, val]) => {
                const formattedKey = formatLabel(key);

                /*
                 * Object values represent grouped scoring factors.
                 * Example:
                 * {
                 *   confidence: 8,
                 *   requirement: 7,
                 *   budget_signal: 0
                 * }
                 */
                if (
                  val !== null &&
                  typeof val === 'object' &&
                  !Array.isArray(val)
                ) {
                  const entries = Object.entries(val);

                  return (
                    <div
                      key={key}
                      className="rounded-lg border border-slate-100 bg-slate-50/70 p-3 space-y-2"
                    >
                      <div className="text-xs font-semibold text-slate-700">
                        {formattedKey}
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
                        {entries.map(([subKey, subValue]) => {
                          const numeric = isNumericValue(subValue);
                          const numericValue = numeric
                            ? Number(subValue)
                            : null;

                          return (
                            <div key={subKey} className="space-y-1">
                              <div className="flex items-center justify-between gap-3 text-xs">
                                <span className="text-slate-500 min-w-0 truncate">
                                  {formatLabel(subKey)}
                                </span>

                                <span className="font-semibold text-slate-800 shrink-0">
                                  {formatValue(subValue)}
                                </span>
                              </div>

                              {numeric &&
                                numericValue !== null &&
                                numericValue >= 0 &&
                                numericValue <= 100 && (
                                  <div className="w-full bg-slate-200 h-1 rounded-full overflow-hidden">
                                    <div
                                      className="bg-teal-600 h-full rounded-full transition-all duration-500"
                                      style={{
                                        width: `${Math.min(
                                          Math.max(numericValue, 0),
                                          100
                                        )}%`,
                                      }}
                                    />
                                  </div>
                                )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                }

                /*
                 * Normal scalar scoring factor.
                 */
                const numeric = isNumericValue(val);
                const numericValue = numeric ? Number(val) : null;

                return (
                  <div key={key} className="space-y-1">
                    <div className="flex items-center justify-between gap-3 text-xs">
                      <span className="text-slate-600 font-medium">
                        {formattedKey}
                      </span>

                      <span className="font-semibold text-slate-800 shrink-0">
                        {formatValue(val)}
                      </span>
                    </div>

                    {numeric &&
                      numericValue !== null &&
                      numericValue >= 0 &&
                      numericValue <= 100 && (
                        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-teal-600 h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.min(
                                Math.max(numericValue, 0),
                                100
                              )}%`,
                            }}
                          />
                        </div>
                      )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Next Best Action */}
        {nextBestAction && (
          <div className="p-3.5 rounded-lg bg-teal-50/70 border border-teal-200 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-teal-900">
              <Info className="w-3.5 h-3.5 text-teal-600" />

              <span>Recommended Next Best Action:</span>

              <span className="bg-teal-100 text-teal-800 px-2 py-0.5 rounded font-bold ml-auto">
                {nextBestAction}
              </span>
            </div>

            {nextBestActionReason && (
              <p className="text-xs text-teal-800/90 pl-5">
                {nextBestActionReason}
              </p>
            )}
          </div>
        )}

        {/* Qualification Summary */}
        {qualificationSummary && (
          <div className="space-y-1 pt-1 border-t border-slate-100">
            <h4 className="text-xs font-semibold text-slate-700">
              AI Qualification Summary
            </h4>

            <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded border border-slate-100">
              {qualificationSummary}
            </p>
          </div>
        )}

      </CardContent>
    </Card>
  );
};
