import { createBrowserRouter, Navigate } from 'react-router-dom';
import { PublicLayout } from '@/layouts/PublicLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { AppLayout } from '@/layouts/AppLayout';
import { ProtectedRoute } from '@/components/common/ProtectedRoute';

// Public Pages
import { LandingRoute } from '@/features/landing/LandingRoute';
import { LoginPage } from '@/features/auth/LoginPage';
import { RegisterPage } from '@/features/auth/RegisterPage';
import { NotFoundPage } from '@/features/auth/NotFoundPage';

// Protected App Pages
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { LeadsPage } from '@/features/leads/LeadsPage';
import { LeadDetailPage } from '@/features/leads/LeadDetailPage';
import { AddLeadPage } from '@/features/leads/AddLeadPage';
import { AIPriorityQueuePage } from '@/features/priority/AIPriorityQueuePage';
import { EnquiriesPage } from '@/features/enquiries/EnquiriesPage';
import { FollowupsPage } from '@/features/followups/FollowupsPage';
import { CustomersPage } from '@/features/customers/CustomersPage';
import { ConversationsPage } from '@/features/conversations/ConversationsPage';
import { CallsPage } from '@/features/calls/CallsPage';
import { AnalyticsPage } from '@/features/analytics/AnalyticsPage';
import { AIReviewPage } from '@/features/ai-review/AIReviewPage';
import { TeamPage } from '@/features/team/TeamPage';
import { ProductsPage } from '@/features/products/ProductsPage';
import { NotificationsPage } from '@/features/notifications/NotificationsPage';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { ProfilePage } from '@/features/profile/ProfilePage';
import { NLSearchPage } from '@/features/search/NLSearchPage';

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/',
    element: <PublicLayout />,
    children: [
      { index: true, element: <LandingRoute /> },
    ],
  },
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },

  // Protected Authenticated CRM App Shell
  {
    path: '/app',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/app/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'enquiries', element: <EnquiriesPage /> },
      { path: 'leads', element: <LeadsPage /> },
      { path: 'leads/new', element: <AddLeadPage /> },
      { path: 'leads/:id', element: <LeadDetailPage /> },
      { path: 'priority', element: <AIPriorityQueuePage /> },
      { path: 'followups', element: <FollowupsPage /> },
      { path: 'customers', element: <CustomersPage /> },
      { path: 'conversations', element: <ConversationsPage /> },
      { path: 'calls', element: <CallsPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'ai-review', element: <AIReviewPage /> },
      { path: 'team', element: <TeamPage /> },
      { path: 'products', element: <ProductsPage /> },
      { path: 'notifications', element: <NotificationsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'search', element: <NLSearchPage /> },
    ],
  },

  // 404 Catch-All
  { path: '*', element: <NotFoundPage /> },
]);
