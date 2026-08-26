import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export const LoadingSpinner: React.FC<{ message?: string; className?: string }> = ({
  message = 'Loading data...',
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-12 text-slate-500', className)}>
      <Loader2 className="w-8 h-8 text-teal-600 animate-spin mb-3" />
      <span className="text-xs font-medium text-slate-600">{message}</span>
    </div>
  );
};
