/**
 * Base API service with Axios instance and interceptors.
 * Handles JWT token attachment and error handling.
 */
import axios from 'axios';
import type { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Token storage key
const TOKEN_STORAGE_KEY = 'nuzlocke_auth_token';

/**
 * Get stored JWT token from localStorage
 */
export const getStoredToken = (): string | null => {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
};

/**
 * Store JWT token in localStorage
 */
export const setStoredToken = (token: string): void => {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

/**
 * Remove JWT token from localStorage
 */
export const removeStoredToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
};

/**
 * Create axios instance with base configuration
 */
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor: attach JWT token to requests
  instance.interceptors.request.use(
    (config) => {
      const token = getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor: handle 401/403 errors
  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response) {
        const status = error.response.status;
        
        // Handle authentication errors
        if (status === 401 || status === 403) {
          // Clear stored token
          removeStoredToken();
          
          // Redirect to login page (only if not already on login page)
          if (window.location.pathname !== '/login' && window.location.pathname !== '/auth/callback') {
            window.location.href = '/login';
          }
        }
      }
      
      return Promise.reject(error);
    }
  );

  return instance;
};

// Export the configured axios instance
export const api = createApiInstance();

/**
 * Typed helper functions for API requests
 */
export const apiHelpers = {
  /**
   * GET request helper
   */
  get: async <T>(url: string, config?: Parameters<typeof api.get>[1]): Promise<T> => {
    const response: AxiosResponse<T> = await api.get(url, config);
    return response.data;
  },

  /**
   * POST request helper
   */
  post: async <T>(
    url: string,
    data?: unknown,
    config?: Parameters<typeof api.post>[2]
  ): Promise<T> => {
    try {
      const response: AxiosResponse<T> = await api.post(url, data, config);
      return response.data;
    } catch (error) {
      // Re-throw with more context for debugging
      console.error(`POST ${url} failed:`, error);
      throw error;
    }
  },

  /**
   * PUT request helper
   */
  put: async <T>(
    url: string,
    data?: unknown,
    config?: Parameters<typeof api.put>[2]
  ): Promise<T> => {
    const response: AxiosResponse<T> = await api.put(url, data, config);
    return response.data;
  },

  /**
   * DELETE request helper
   */
  delete: async <T>(url: string, config?: Parameters<typeof api.delete>[1]): Promise<T> => {
    const response: AxiosResponse<T> = await api.delete(url, config);
    return response.data;
  },

  /**
   * PATCH request helper
   */
  patch: async <T>(
    url: string,
    data?: unknown,
    config?: Parameters<typeof api.patch>[2]
  ): Promise<T> => {
    const response: AxiosResponse<T> = await api.patch(url, data, config);
    return response.data;
  },
};

