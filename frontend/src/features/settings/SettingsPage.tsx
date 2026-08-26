import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Building, Cpu, Share2 } from 'lucide-react';
import { organizationApi } from '@/api/organization';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Tabs } from '@/components/ui/Tabs';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState('general');

  const { data: org, isLoading } = useQuery({
    queryKey: ['organization'],
    queryFn: () => organizationApi.getCurrent(),
  });

  const [name, setName] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [timezone, setTimezone] = useState('UTC');

  useEffect(() => {
    if (org) {
      setName(org.name);
      setCurrency(org.currency || 'USD');
      setTimezone(org.timezone || 'UTC');
    }
  }, [org]);

  const updateMutation = useMutation({
    mutationFn: () =>
      organizationApi.updateCurrent({
        name,
        currency,
        timezone,
      }),
    onSuccess: () => {
      success('Settings Saved', 'Organization profile updated.');
      queryClient.invalidateQueries({ queryKey: ['organization'] });
    },
    onError: (err: any) => {
      error('Update Failed', err.message || 'Could not update organization.');
    },
  });

  const tabs = [
    { id: 'general', label: 'General & Organization' },
    { id: 'integrations', label: 'Omnichannel Integrations' },
    { id: 'ai', label: 'AI Intelligence Config' },
  ];

  if (isLoading) {
    return <LoadingSpinner message="Fetching organization settings..." />;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Organization Settings</h2>
        <p className="text-xs text-slate-500 mt-1">
          Configure CRM defaults, currency, timezones, and AI models.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'general' && (
        <Card className="p-6 bg-white space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Building className="w-4 h-4 text-teal-600" /> Organization Profile
          </h3>

          <Input
            label="Organization Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Operating Currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              placeholder="USD, EUR, INR"
            />
            <Input
              label="System Timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="UTC, America/New_York"
            />
          </div>

          <div className="flex justify-end pt-4">
            <Button
              variant="primary"
              onClick={() => updateMutation.mutate()}
              isLoading={updateMutation.isPending}
            >
              Save Organization Settings
            </Button>
          </div>
        </Card>
      )}

      {activeTab === 'integrations' && (
        <Card className="p-6 bg-white space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Share2 className="w-4 h-4 text-teal-600" /> Channel Integrations
          </h3>

          <div className="space-y-3">
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-slate-900">WhatsApp Business Cloud API</h4>
                <p className="text-xs text-slate-500">Inbound lead capture and automated response sync.</p>
              </div>
              <span className="px-2.5 py-1 rounded text-xs font-bold bg-emerald-100 text-emerald-800">
                Connected
              </span>
            </div>

            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-slate-900">Instagram Messaging API</h4>
                <p className="text-xs text-slate-500">Direct message triage and intent classification.</p>
              </div>
              <span className="px-2.5 py-1 rounded text-xs font-bold bg-emerald-100 text-emerald-800">
                Connected
              </span>
            </div>

            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-slate-900">Meta Lead Ads Webhooks</h4>
                <p className="text-xs text-slate-500">Instant ad form submission intake.</p>
              </div>
              <span className="px-2.5 py-1 rounded text-xs font-bold bg-emerald-100 text-emerald-800">
                Active
              </span>
            </div>
          </div>
        </Card>
      )}

      {activeTab === 'ai' && (
        <Card className="p-6 bg-white space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Cpu className="w-4 h-4 text-teal-600" /> AI Intelligence Pipeline Architecture
          </h3>

          <div className="space-y-3 text-xs text-slate-700">
            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="font-bold text-slate-900 block">LLM Engine</span>
              <span>Google Gemini API via LangGraph multi-step workflows.</span>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="font-bold text-slate-900 block">Speech-to-Text Engine</span>
              <span>Faster-Whisper Large-v3 with GPU acceleration.</span>
            </div>

            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="font-bold text-slate-900 block">Vector Indexing & Embeddings</span>
              <span>pgvector with semantic search threshold index.</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
