import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { teamApi } from '@/api/team';
import { UserRole, UserResponse } from '@/types/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Select } from '@/components/ui/Select';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';

export const TeamPage: React.FC = () => {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [editingUser, setEditingUser] = useState<UserResponse | null>(null);
  const [selectedRole, setSelectedRole] = useState<UserRole>(UserRole.SALES);
  const [isActive, setIsActive] = useState<boolean>(true);

  const { data: members = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['team'],
    queryFn: () => teamApi.list(),
  });

  // Update Mutation
  const updateMutation = useMutation({
    mutationFn: () =>
      teamApi.update(editingUser!.id, {
        role: selectedRole,
        is_active: isActive,
      }),
    onSuccess: () => {
      success('Team Member Updated', 'User role and permissions updated.');
      setEditingUser(null);
      queryClient.invalidateQueries({ queryKey: ['team'] });
    },
    onError: (err: any) => {
      error('Update Failed', err.message || 'Could not update team member.');
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Fetching sales team members..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Unable to load team"
        description="Could not connect to the user management API."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Team & Sales Representatives</h2>
          <p className="text-xs text-slate-500 mt-1">
            Organization team members, role assignments, and active statuses.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh Team
        </Button>
      </div>

      {/* Team Table */}
      <Card className="overflow-hidden bg-white">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-4">Member Name</th>
                <th className="py-3 px-4">Email Address</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Status</th>
                {isAdmin && <th className="py-3 px-4 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs sm:text-sm text-slate-700">
              {members.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-900">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center">
                        {m.full_name.charAt(0)}
                      </div>
                      <span>{m.full_name}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600">{m.email}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        m.role === UserRole.ADMIN ? 'bg-indigo-100 text-indigo-800' : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    {m.is_active ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 text-xs font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-slate-400 text-xs">
                        <XCircle className="w-3.5 h-3.5" /> Inactive
                      </span>
                    )}
                  </td>
                  {isAdmin && (
                    <td className="py-3.5 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditingUser(m);
                          setSelectedRole(m.role);
                          setIsActive(m.is_active);
                        }}
                      >
                        Manage Role
                      </Button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Edit Role Modal */}
      <Modal isOpen={!!editingUser} onClose={() => setEditingUser(null)} title="Manage Team Member Access">
        <div className="space-y-4">
          <p className="text-xs text-slate-600 font-semibold">{editingUser?.full_name} ({editingUser?.email})</p>

          <Select
            label="Assigned User Role"
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value as UserRole)}
            options={Object.values(UserRole).map((r) => ({ label: r, value: r }))}
          />

          <label className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
            />
            Account Active
          </label>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setEditingUser(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => updateMutation.mutate()}
              isLoading={updateMutation.isPending}
            >
              Save Changes
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
