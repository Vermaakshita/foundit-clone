import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { login as apiLogin, logout as apiLogout, register as apiRegister, getMe } from '../api/auth';
import { tokenStorage } from '../api/client';
import type { RegisterData, User } from '../types';

// ─── Context Shape ────────────────────────────────────────────────────────────

interface AuthContextValue {
  /** The currently authenticated user, or null if not logged in. */
  user: User | null;
  /** True while the initial session restore or an auth operation is in progress. */
  isLoading: boolean;
  /** True when a user is authenticated (token present + user loaded). */
  isAuthenticated: boolean;
  /** Authenticates the user with email + password. */
  login: (email: string, password: string) => Promise<void>;
  /** Registers a new account and logs in the resulting user. */
  register: (data: RegisterData) => Promise<void>;
  /** Logs out the current user and clears the session. */
  logout: () => Promise<void>;
  /** Refreshes the in-memory user object from the server. */
  refreshUser: () => Promise<void>;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore session on mount: if a token exists in localStorage, fetch the user
  useEffect(() => {
    const token = tokenStorage.getAccess();
    if (!token) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    getMe()
      .then((fetchedUser) => {
        if (!cancelled) setUser(fetchedUser);
      })
      .catch(() => {
        // Token is invalid / expired and refresh failed — clear everything
        tokenStorage.clear();
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // ─── Auth Actions ────────────────────────────────────────────────────────

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const { user: loggedInUser } = await apiLogin(email, password);
      setUser(loggedInUser);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (data: RegisterData): Promise<void> => {
    setIsLoading(true);
    try {
      const { user: newUser } = await apiRegister(data);
      setUser(newUser);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await apiLogout();
    } finally {
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  const refreshUser = useCallback(async (): Promise<void> => {
    try {
      const freshUser = await getMe();
      setUser(freshUser);
    } catch {
      // If refresh fails, leave the current user in place
    }
  }, []);

  // ─── Memoised Value ──────────────────────────────────────────────────────

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, isLoading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

/**
 * Returns the current auth context.
 * Must be called inside an <AuthProvider>.
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
