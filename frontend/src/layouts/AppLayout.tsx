import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';

const titleMap: Record<string, string> = {
  '/app/dashboard': 'Operational Dashboard',
  '/app/enquiries': 'Omnichannel Enquiries Inbox',
  '/app/leads': 'Sales Leads Management',
  '/app/leads/new': 'Create New Sales Lead',
  '/app/priority': 'AI Priority Queue & Explainability',
  '/app/followups': 'Follow-Ups Management',
  '/app/customers': 'Customer Directory',
  '/app/calls': 'Call Intelligence & Transcripts',
  '/app/ai-review': 'AI Human-in-the-Loop Review Queue',
  '/app/search': 'AI Natural-Language Search',
  '/app/analytics': 'Analytics & Performance Reports',
  '/app/team': 'Team & Sales Representatives',
  '/app/products': 'Product Catalog Management',
  '/app/notifications': 'Notifications Center',
  '/app/settings': 'Organization Settings',
  '/app/profile': 'User Profile & Account',
};

export const AppLayout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  const title = titleMap[location.pathname] || 'OmniLead AI';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
      {/* Left Sidebar */}
      <AppSidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <AppHeader pageTitle={title} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
