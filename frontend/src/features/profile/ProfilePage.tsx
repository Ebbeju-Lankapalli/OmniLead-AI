import React from 'react';
import { Mail, Shield, Building, LogOut, CheckCircle2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">User Account Profile</h2>
        <p className="text-xs text-slate-500 mt-1">
          Your personal credentials, organizational scope, and system privileges.
        </p>
      </div>

      <Card className="p-6 bg-white space-y-6">
        <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
          <div className="w-16 h-16 rounded-full bg-slate-100 text-slate-800 flex items-center justify-center font-bold text-2xl border-2 border-slate-200">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">{user?.full_name}</h3>
            <p className="text-xs text-slate-500">{user?.email}</p>
            <span className="inline-block mt-2 px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-teal-50 text-teal-800 border border-teal-200">
              {user?.role}
            </span>
          </div>
        </div>

        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500 flex items-center gap-2">
              <Mail className="w-4 h-4 text-slate-400" /> Email Address
            </span>
            <span className="font-semibold text-slate-800">{user?.email}</span>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500 flex items-center gap-2">
              <Shield className="w-4 h-4 text-slate-400" /> User Role
            </span>
            <span className="font-semibold text-slate-800">{user?.role}</span>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500 flex items-center gap-2">
              <Building className="w-4 h-4 text-slate-400" /> Organization ID
            </span>
            <span className="font-mono text-slate-600 text-[11px]">{user?.organization_id}</span>
          </div>

          <div className="flex items-center justify-between py-2">
            <span className="text-slate-500 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Account Status
            </span>
            <span className="font-semibold text-emerald-700">Active & Verified</span>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <Button variant="outline" onClick={logout} className="text-rose-600 border-rose-200 hover:bg-rose-50">
            <LogOut className="w-4 h-4 mr-1.5" /> Sign Out of Workspace
          </Button>
        </div>
      </Card>
    </div>
  );
};
