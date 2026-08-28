import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from 'react';
import { AuthenticatedUser, UserRole } from '@/types/api';
import { authApi, LoginParams, RegisterParams } from '@/api/auth';
import { setAccessTokenGetter } from '@/api/client';
import { supabase } from '@/lib/supabase';

interface AuthContextType {
  user: AuthenticatedUser | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (data: LoginParams) => Promise<void>;
  register: (data: RegisterParams) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /*
   * Keep Axios synchronized with the current Supabase access token.
   */
  useEffect(() => {
    setAccessTokenGetter(() => accessToken);
  }, [accessToken]);

  /*
   * Load the OmniLead application user using the current
   * Supabase session.
   */
  const loadUserFromSession = useCallback(
    async (token: string | null) => {
      if (!token) {
        setUser(null);
        setAccessToken(null);
        return;
      }

      try {
        /*
         * The backend validates the Supabase access token and
         * resolves the OmniLead organization/user.
         */
        const response = await authApi.getMe();

        setUser(response.user);
        setAccessToken(token);
      } catch (error) {
        console.error('Unable to validate application session:', error);

        /*
         * Supabase owns the refresh-token lifecycle.
         * Try to obtain the newest session before signing out.
         */
        const {
          data: { session },
          error: refreshError,
        } = await supabase.auth.refreshSession();

        if (refreshError || !session) {
          console.error(
            'Unable to refresh Supabase session:',
            refreshError
          );

          await supabase.auth.signOut();

          setUser(null);
          setAccessToken(null);
          return;
        }

        try {
          const refreshedUser = await authApi.getMe();

          setUser(refreshedUser.user);
          setAccessToken(session.access_token);
        } catch (finalError) {
          console.error(
            'Unable to validate refreshed session:',
            finalError
          );

          await supabase.auth.signOut();

          setUser(null);
          setAccessToken(null);
        }
      }
    },
    []
  );

  /*
   * Initialize the persisted Supabase session.
   */
  useEffect(() => {
    let mounted = true;

    const initialize = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession();

        if (!mounted) return;

        if (error) {
          console.error(
            'Unable to restore authentication session:',
            error
          );

          setUser(null);
          setAccessToken(null);
          return;
        }

        await loadUserFromSession(
          session?.access_token ?? null
        );
      } catch (error) {
        console.error(
          'Authentication initialization failed:',
          error
        );

        if (mounted) {
          setUser(null);
          setAccessToken(null);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    void initialize();

    /*
     * Keep all browser tabs synchronized with Supabase's
     * authentication state.
     */
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (!mounted) return;

        if (event === 'SIGNED_OUT') {
          setUser(null);
          setAccessToken(null);
          return;
        }

        if (
          event === 'SIGNED_IN' ||
          event === 'TOKEN_REFRESHED' ||
          event === 'INITIAL_SESSION'
        ) {
          const token = session?.access_token ?? null;

          setAccessToken(token);

          /*
           * Don't perform another backend request for
           * SIGNED_IN here because login() already loaded
           * the application user.
           *
           * For TOKEN_REFRESHED, only the token changes.
           */
        }
      }
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [loadUserFromSession]);

  /*
   * Login through the OmniLead backend, then hand the returned
   * Supabase session to the browser Supabase client.
   */
  const login = async (data: LoginParams) => {
    setIsLoading(true);

    try {
      const response = await authApi.login(data);

      if (
        !response.access_token ||
        !response.refresh_token
      ) {
        throw new Error(
          'Authentication succeeded but no complete session was returned.'
        );
      }

      const { data: sessionData, error } =
        await supabase.auth.setSession({
          access_token: response.access_token,
          refresh_token: response.refresh_token,
        });

      if (error || !sessionData.session) {
        throw (
          error ??
          new Error('Unable to persist authentication session.')
        );
      }

      setAccessToken(
        sessionData.session.access_token
      );

      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  /*
   * Registration follows the same session-persistence flow.
   */
  const register = async (data: RegisterParams) => {
    setIsLoading(true);

    try {
      const response = await authApi.register(data);

      if (
        !response.access_token ||
        !response.refresh_token
      ) {
        throw new Error(
          'Registration succeeded but no complete session was returned.'
        );
      }

      const { data: sessionData, error } =
        await supabase.auth.setSession({
          access_token: response.access_token,
          refresh_token: response.refresh_token,
        });

      if (error || !sessionData.session) {
        throw (
          error ??
          new Error('Unable to persist authentication session.')
        );
      }

      setAccessToken(
        sessionData.session.access_token
      );

      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  /*
   * Sign out from Supabase so the persisted session is removed
   * and other browser tabs receive the sign-out event.
   */
  const logout = useCallback(async () => {
    await supabase.auth.signOut();

    setAccessToken(null);
    setUser(null);
  }, []);

  /*
   * Revalidate the current session against the backend.
   */
  const refreshUser = useCallback(async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    await loadUserFromSession(
      session?.access_token ?? null
    );
  }, [loadUserFromSession]);

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

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      'useAuth must be used within an AuthProvider'
    );
  }

  return context;
};
