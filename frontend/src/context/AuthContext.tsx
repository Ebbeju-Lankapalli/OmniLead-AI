import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { AuthenticatedUser, UserRole } from '@/types/api';
import { authApi, LoginParams, RegisterParams } from '@/api/auth';
import { setAccessTokenGetter } from '@/api/client';

interface AuthContextType {
  user: AuthenticatedUser | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (data: LoginParams) => Promise<void>;
  register: (data: RegisterParams) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(() => {
    return localStorage.getItem('omnilead_access_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Sync access token getter with API client
  useEffect(() => {
    setAccessTokenGetter(() => accessToken);
  }, [accessToken]);

  const logout = useCallback(() => {
    localStorage.removeItem('omnilead_access_token');
    localStorage.removeItem('omnilead_refresh_token');
    setAccessToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('omnilead_access_token');
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const session = await authApi.getMe();
      setUser(session.user);
      if (session.access_token) {
        setAccessToken(session.access_token);
        localStorage.setItem('omnilead_access_token', session.access_token);
      }
    } catch (error) {
      console.error('Session validation error:', error);
      // Attempt refresh token if present
      const refreshToken = localStorage.getItem('omnilead_refresh_token');
      if (refreshToken) {
        try {
          const res = await authApi.refreshSession(refreshToken);
          localStorage.setItem('omnilead_access_token', res.access_token);
          setAccessToken(res.access_token);
          if (res.refresh_token) {
            localStorage.setItem('omnilead_refresh_token', res.refresh_token);
          }
          const session = await authApi.getMe();
          setUser(session.user);
        } catch {
          logout();
        }
      } else {
        logout();
      }
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (data: LoginParams) => {
    setIsLoading(true);
    try {
      const res = await authApi.login(data);
      if (res.access_token) {
        localStorage.setItem('omnilead_access_token', res.access_token);
        setAccessToken(res.access_token);
      }
      if (res.refresh_token) {
        localStorage.setItem('omnilead_refresh_token', res.refresh_token);
      }
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterParams) => {
    setIsLoading(true);
    try {
      const res = await authApi.register(data);
      if (res.access_token) {
        localStorage.setItem('omnilead_access_token', res.access_token);
        setAccessToken(res.access_token);
      }
      if (res.refresh_token) {
        localStorage.setItem('omnilead_refresh_token', res.refresh_token);
      }
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    accessToken,
    isLoading,
    isAuthenticated: !!user,
    isAdmin: user?.role === UserRole.ADMIN,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
