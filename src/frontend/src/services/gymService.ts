/**
 * Gym management service.
 * Handles gym progression and trainer data.
 */
import { apiHelpers } from './api';
import type { GymProgressResponse, GymProgressEntry } from '../types/gym';

export interface GymProgressApiResponse {
  Progress: GymProgressEntry[];
}

export interface AddGymResponse {
  created: GymProgressEntry;
}

export interface VersionGymsResponse {
  gyms: unknown[]; // Gym models from backend
}

/**
 * Get gym progress for a game file
 */
export const getGymProgress = async (gameFileId: number): Promise<GymProgressEntry[]> => {
  const response = await apiHelpers.get<GymProgressApiResponse>(
    `/api/gyms/game-files/${gameFileId}/gym-progress`
  );
  return response.Progress;
};

/**
 * Get upcoming gyms for a game file
 */
export const getUpcomingGyms = async (gameFileId: number): Promise<GymProgressResponse> => {
  return await apiHelpers.get<GymProgressResponse>(
    `/api/gyms/game-files/${gameFileId}/upcoming-gyms`
  );
};

/**
 * Mark a gym as completed
 */
export const addGym = async (
  gameFileId: number,
  gymNumber: number
): Promise<AddGymResponse> => {
  return await apiHelpers.post<AddGymResponse>(
    `/api/gyms/game-files/${gameFileId}/add-gym/${gymNumber}`
  );
};

/**
 * Get all gyms for a version
 */
export const getVersionGyms = async (versionName: string): Promise<unknown[]> => {
  const response = await apiHelpers.get<VersionGymsResponse>(
    `/api/gyms/version/${versionName}/gyms`
  );
  return response.gyms;
};

