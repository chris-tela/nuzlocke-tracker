/**
 * User management service.
 * Handles user profile operations.
 */
import { apiHelpers } from './api';
import type { User } from '../types';

export interface UserUpdate {
  username?: string;
  email?: string;
}

/**
 * Get current user profile
 */
export const getCurrentUser = async (): Promise<User> => {
  return await apiHelpers.get<User>('/api/users/me');
};

/**
 * Update current user profile
 */
export const updateCurrentUser = async (updateData: UserUpdate): Promise<User> => {
  return await apiHelpers.put<User>('/api/users/me', updateData);
};

