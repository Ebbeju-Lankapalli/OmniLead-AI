import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Inbox,
  Users,
  Flame,
  CalendarCheck,
  UserCheck,
  PhoneCall,
  BrainCircuit,
  Search,
  BarChart3,
  Users2,
  Package,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';

interface AppSidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const AppSidebar: React.FC<AppSidebarProps> = ({ collapsed, onToggleCollapse }) => {
  const location = useLocation();
  const { isAdmin } = useAuth();

  const navItems = [
    { label: 'Dashboard', path: '/app/dashboard', icon: LayoutDashboard },
    { label: 'Enquiries', path: '/app/enquiries', icon: Inbox },
    { label: 'Leads', path: '/app/leads', icon: Users },
    { label: 'AI Priority Queue', path: '/app/priority', icon: Flame, badge: 'AI' },
    { label: 'Follow-Ups', path: '/app/followups', icon: CalendarCheck },
    { label: 'Customers', path: '/app/customers', icon: UserCheck },
    { label: 'Calls', path: '/app/calls', icon: PhoneCall },
    { label: 'AI Review Queue', path: '/app/ai-review', icon: BrainCircuit, badge: 'Review' },
    { label: 'NL Lead Search', path: '/app/search', icon: Search },
    { label: 'Analytics', path: '/app/analytics', icon: BarChart3 },
    ...(isAdmin
      ? [
          { label: 'Team', path: '/app/team', icon: Users2 },
          { label: 'Products', path: '/app/products', icon: Package },
        ]
      : []),
    { label: 'Notifications', path: '/app/notifications', icon: Bell },
    { label: 'Settings', path: '/app/settings', icon: Settings },
  ];

  return (
    <aside
      className={cn(
        'relative z-30 flex flex-col bg-slate-900 text-slate-300 border-r border-slate-800 transition-all duration-300 select-none shrink-0',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800 bg-slate-950/50">
        <NavLink to="/app/dashboard" className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold text-base shrink-0 shadow-sm">
            O
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="font-bold text-sm tracking-tight text-white truncate">OmniLead AI</span>
              <span className="text-[10px] text-teal-400 font-medium tracking-wide uppercase">Lead Intelligence</span>
            </div>
          )}
        </NavLink>

        <button
          onClick={onToggleCollapse}
          className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors hidden md:flex"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-all group relative',
                isActive
                  ? 'bg-teal-600/90 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-white' : 'text-slate-400 group-hover:text-white')} />
              {!collapsed && <span className="truncate flex-1">{item.label}</span>}
              {!collapsed && item.badge && (
                <span
                  className={cn(
                    'px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                    isActive ? 'bg-teal-700 text-white' : 'bg-slate-800 text-teal-400 border border-slate-700'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>
    </aside>
  );
};
