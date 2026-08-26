import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-teal-50 border border-teal-200 text-teal-600 flex items-center justify-center mb-6 shadow-sm">
        <FileQuestion className="w-8 h-8" />
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-slate-900">404 - Page Not Found</h1>
      <p className="text-slate-600 mt-2 max-w-md text-sm">
        The page or resource you are looking for does not exist or has been moved.
      </p>
      <div className="mt-6 flex items-center gap-3">
        <Link to="/app/dashboard">
          <Button variant="primary" className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};
