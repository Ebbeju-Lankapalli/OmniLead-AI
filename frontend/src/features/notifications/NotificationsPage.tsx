import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCheck, RefreshCw } from 'lucide-react';
import { notificationsApi } from '@/api/notifications';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { formatDateTime } from '@/lib/utils';

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success } = useToast();

  const [unreadOnly, setUnreadOnly] = useState(false);

  const { data: notifications = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['notifications-list', unreadOnly],
    queryFn: () => notificationsApi.list({ unread_only: unreadOnly }),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications-list'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-counts'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      success('Notifications Cleared', 'All notifications marked as read.');
      queryClient.invalidateQueries({ queryKey: ['notifications-list'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-counts'] });
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Fetching notifications..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Unable to load notifications"
        description="Could not connect to notifications endpoint."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Notifications Center</h2>
          <p className="text-xs text-slate-500 mt-1">
            System alerts, AI review flags, and overdue follow-up reminders.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => markAllReadMutation.mutate()} isLoading={markAllReadMutation.isPending}>
            <CheckCheck className="w-4 h-4 mr-1.5" /> Mark All Read
          </Button>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setUnreadOnly(false)}
          className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
            !unreadOnly ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All Notifications
        </button>
        <button
          onClick={() => setUnreadOnly(true)}
          className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
            unreadOnly ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Unread Only
        </button>
      </div>

      {/* List */}
      {notifications.length === 0 ? (
        <EmptyState title="No notifications" description="You're all caught up! No notifications to display." />
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => (
            <Card
              key={n.id}
              className={`p-4 bg-white border transition-all ${
                !n.read_at ? 'border-teal-200 bg-teal-50/20' : 'border-slate-200'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">{n.title}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-600">
                      {n.channel}
                    </span>
                    {!n.read_at && <span className="w-2 h-2 rounded-full bg-teal-600" />}
                  </div>

                  <p className="text-xs text-slate-700">{n.body || n.message}</p>
                  <span className="text-[11px] text-slate-400 block pt-1">{formatDateTime(n.created_at)}</span>
                </div>

                {!n.read_at && (
                  <Button variant="ghost" size="sm" onClick={() => markReadMutation.mutate(n.id)}>
                    Mark Read
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
