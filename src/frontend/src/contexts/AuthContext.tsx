/**
 * Authentication Context
 * Manages user authentication state, token, and auth operations
 */
import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { getStoredToken, setStoredToken, removeStoredToken } from '../services/api';
import { login as loginService, register as registerService, logout as logoutService, getCurrentUser as getCurrentUserService, initiateGoogleLogin } from '../services/authService';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loginWithGoogle: (mode?: 'login' | 'register') => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token and user on mount
  useEffect(() => {
    const loadAuth = async () => {
      const storedToken = getStoredToken();
      if (storedToken) {
        setToken(storedToken);
        try {
          const currentUser = await getCurrentUserService();
          setUser(currentUser);
        } catch (error) {
          // Token is invalid, clear it
          removeStoredToken();
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    loadAuth();
  }, []);

  // Handle OAuth callback from URL
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const tokenParam = urlParams.get('token');
      
      if (tokenParam) {
        setStoredToken(tokenParam);
        setToken(tokenParam);
        try {
          const currentUser = await getCurrentUserService();
          setUser(currentUser);
          // Clean up URL
          window.history.replaceState({}, document.title, window.location.pathname);
        } catch (error) {
          console.error('Failed to get user after OAuth:', error);
        }
      }
    };

    handleOAuthCallback();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await loginService({ username, password });
    setStoredToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  };

  const register = async (username: string, password: string) => {
    const response = await registerService({ username, password });
    setStoredToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  };

  const logout = async () => {
    await logoutService();
    removeStoredToken();
    setToken(null);
    setUser(null);
  };

  const loginWithGoogle = async (mode: 'login' | 'register' = 'register') => {
    await initiateGoogleLogin(mode);
  };

  const refreshUser = async () => {
    if (token) {
      try {
        const currentUser = await getCurrentUserService();
        setUser(currentUser);
      } catch (error) {
        console.error('Failed to refresh user:', error);
        // Token might be invalid, logout
        await logout();
      }
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    register,
    logout,
    loginWithGoogle,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

