import React from 'react';
import { Outlet, Link } from 'react-router-dom';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
            O
          </div>
          <span className="text-2xl font-bold tracking-tight text-slate-900">OmniLead AI</span>
        </Link>
        <p className="mt-2 text-xs font-semibold uppercase tracking-wider text-teal-700">
          Omnichannel Lead Intelligence Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl border border-slate-200 sm:rounded-lg sm:px-10">
          <Outlet />
        </div>
      </div>
    </div>
  );
};
