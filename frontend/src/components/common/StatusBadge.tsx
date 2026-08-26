import React from 'react';
import { Badge } from '@/components/ui/Badge';
import {
  getPurchaseIntentBadge,
  getLeadSourceBadge,
  getFollowUpStatusBadge,
  getEnquiryStatusBadge,
  getScoreColor,
} from '@/lib/utils';
import { PurchaseIntent, LeadSource, FollowUpStatus, EnquiryStatus } from '@/types/api';

export const PurchaseIntentBadge: React.FC<{ intent?: PurchaseIntent | string | null }> = ({ intent }) => {
  const { label, className } = getPurchaseIntentBadge(intent);
  return <Badge className={className}>{label}</Badge>;
};

export const LeadSourceBadge: React.FC<{ source?: LeadSource | string | null }> = ({ source }) => {
  const { label, className } = getLeadSourceBadge(source);
  return <Badge className={className}>{label}</Badge>;
};

export const FollowUpStatusBadge: React.FC<{ status: FollowUpStatus | string }> = ({ status }) => {
  const { label, className } = getFollowUpStatusBadge(status);
  return <Badge className={className}>{label}</Badge>;
};

export const EnquiryStatusBadge: React.FC<{ status: EnquiryStatus | string }> = ({ status }) => {
  const { label, className } = getEnquiryStatusBadge(status);
  return <Badge className={className}>{label}</Badge>;
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  return <Badge className="bg-slate-100 text-slate-800 border-slate-200">{status}</Badge>;
};

export const PriorityBadge: React.FC<{ score?: number | null }> = ({ score }) => {
  const { text, bg, border } = getScoreColor(score);
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold border ${bg} ${text} ${border}`}>
      Priority: {score !== null && score !== undefined ? Math.round(score) : 'N/A'}
    </span>
  );
};

