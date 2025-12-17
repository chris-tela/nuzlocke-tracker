/**
 * Error handling utilities
 * Extracts user-friendly error messages from API errors
 */
import type { AxiosError } from 'axios';

interface ApiErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

/**
 * Extract user-friendly error message from an error
 */
export const getErrorMessage = (error: unknown): string => {
  // Handle Axios errors
  if (error && typeof error === 'object' && 'isAxiosError' in error) {
    const axiosError = error as AxiosError<ApiErrorResponse>;
    
    if (axiosError.response?.data) {
      const data = axiosError.response.data;
      
      // Try to get detail first (FastAPI standard)
      if (data.detail) {
        return data.detail;
      }
      
      // Try message
      if (data.message) {
        return data.message;
      }
      
      // Try error
      if (data.error) {
        return data.error;
      }
      
      // If data is a string
      if (typeof data === 'string') {
        return data;
      }
    }
    
    // Fallback to status text
    if (axiosError.response?.statusText) {
      return axiosError.response.statusText;
    }
  }
  
  // Handle regular Error objects
  if (error instanceof Error) {
    return error.message;
  }
  
  // Fallback
  return 'An unexpected error occurred';
};

