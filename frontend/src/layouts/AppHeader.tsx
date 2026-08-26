import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, LogOut, User as UserIcon, Sparkles } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { notificationsApi } from '@/api/notifications';
import { useQuery } from '@tanstack/react-query';

export interface AppHeaderProps {
  pageTitle?: string;
  onMobileMenuToggle?: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ pageTitle = 'Dashboard' }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Notifications unread count
  const { data: notificationCounts } = useQuery({
    queryKey: ['notifications-counts'],
    queryFn: () => notificationsApi.getCounts(),
    refetchInterval: 30000,
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/app/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between z-20 shrink-0">
      {/* Left: Page Title */}
      <div className="flex items-center gap-4">
        <h1 className="text-base font-bold text-slate-900 tracking-tight">{pageTitle}</h1>
      </div>

      {/* Center: Global Natural-Language Quick Search */}
      <form onSubmit={handleSearchSubmit} className="hidden lg:flex items-center w-full max-w-md mx-4">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Ask AI e.g. 'High intent leads from WhatsApp'..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:bg-white transition-all"
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-teal-600"
            title="Execute Search"
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
          </button>
        </div>
      </form>

      {/* Right: Actions, Notifications & Profile */}
      <div className="flex items-center gap-3">
        {/* Notifications Icon */}
        <button
          onClick={() => navigate('/app/notifications')}
          className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
          title="Notifications"
        >
          <Bell className="w-5 h-5" />
          {notificationCounts && notificationCounts.unread > 0 && (
            <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-rose-600 text-white font-bold text-[10px] rounded-full flex items-center justify-center border border-white">
              {notificationCounts.unread > 9 ? '9+' : notificationCounts.unread}
            </span>
          )}
        </button>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2.5 p-1.5 rounded-md hover:bg-slate-100 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-semibold text-xs border border-slate-300">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="hidden md:flex flex-col text-left">
              <span className="text-xs font-semibold text-slate-900 leading-none">{user?.full_name}</span>
              <span className="text-[10px] font-medium text-slate-500 uppercase mt-0.5">{user?.role}</span>
            </div>
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50 animate-fadeIn">
              <div className="px-4 py-2 border-b border-slate-100">
                <p className="text-xs font-semibold text-slate-900 truncate">{user?.full_name}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
              </div>
              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  navigate('/app/profile');
                }}
                className="w-full flex items-center gap-2 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <UserIcon className="w-4 h-4 text-slate-400" />
                <span>My Profile</span>
              </button>
              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  logout();
                }}
                className="w-full flex items-center gap-2 px-4 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 transition-colors border-t border-slate-100"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
