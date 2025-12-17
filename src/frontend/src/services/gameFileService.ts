/**
 * Game file management service.
 * Handles game file CRUD operations.
 */
import { apiHelpers } from './api';
import type { GameFile } from '../types';

export interface GameFileCreate {
  trainer_name: string;
  game_name: string;
}

/**
 * Create a new game file
 */
export const createGameFile = async (gameFile: GameFileCreate): Promise<GameFile> => {
  return await apiHelpers.post<GameFile>('/api/game-files', gameFile);
};

/**
 * Get all game files for the current user
 */
export const getGameFiles = async (): Promise<GameFile[]> => {
  return await apiHelpers.get<GameFile[]>('/api/game-files');
};

/**
 * Get a specific game file by ID
 */
export const getGameFile = async (gameFileId: number): Promise<GameFile> => {
  return await apiHelpers.get<GameFile>(`/api/game-files/${gameFileId}`);
};

/**
 * Update a game file (trainer name/game name)
 * Note: This endpoint is not yet implemented in the backend
 */
export const updateGameFile = async (
  gameFileId: number,
  updateData: Partial<GameFileCreate>
): Promise<GameFile> => {
  return await apiHelpers.put<GameFile>(`/api/game-files/${gameFileId}`, updateData);
};

/**
 * Delete a game file
 */
export const deleteGameFile = async (gameFileId: number): Promise<void> => {
  await apiHelpers.delete(`/api/game-files/${gameFileId}`);
};

