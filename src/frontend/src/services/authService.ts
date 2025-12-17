/**
 * Authentication service for JWT and OAuth flows.
 * Handles login, registration, OAuth callbacks, and token management.
 */
import { apiHelpers, setStoredToken, removeStoredToken } from './api';
import type { User } from '../types';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserRegister {
  username: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface GoogleLoginResponse {
  url: string;
}

/**
 * Register a new user with username and password
 */
export const register = async (userData: UserRegister): Promise<TokenResponse> => {
  const response = await apiHelpers.post<TokenResponse>('/api/auth/register', userData);
  setStoredToken(response.access_token);
  return response;
};

/**
 * Login with username and password
 */
export const login = async (userData: UserLogin): Promise<TokenResponse> => {
  const response = await apiHelpers.post<TokenResponse>('/api/auth/login', userData);
  setStoredToken(response.access_token);
  return response;
};

/**
 * Logout (client-side token removal)
 */
export const logout = async (): Promise<void> => {
  try {
    await apiHelpers.post('/api/auth/logout');
  } finally {
    removeStoredToken();
  }
};

/**
 * Get Google OAuth login URL
 */
export const getGoogleLoginUrl = async (mode: 'login' | 'register' = 'register'): Promise<string> => {
  try {
    const response = await apiHelpers.get<GoogleLoginResponse>(`/api/auth/google/login?mode=${mode}`);
    return response.url;
  } catch (error) {
    console.error('Failed to get Google login URL:', error);
    throw error;
  }
};

/**
 * Initiate Google OAuth login flow
 * Redirects browser to Google OAuth page
 */
export const initiateGoogleLogin = async (mode: 'login' | 'register' = 'register'): Promise<void> => {
  const url = await getGoogleLoginUrl(mode);
  window.location.href = url;
};

/**
 * Handle OAuth callback
 * The backend redirects to frontend with token in query params
 * This function extracts and stores the token
 */
export const handleOAuthCallback = (token: string): void => {
  setStoredToken(token);
};

/**
 * Get current authenticated user
 */
export const getCurrentUser = async (): Promise<User> => {
  return await apiHelpers.get<User>('/api/auth/me');
};

