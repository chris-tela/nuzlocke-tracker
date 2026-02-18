/**
 * Save file import service.
 * Handles uploading .sav files and creating/updating game files from them.
 */
import { api } from './api';
import type { ParsedSavePreview, GameFile } from '../types';

/**
 * Upload and parse a .sav file, returning a preview of the contents.
 */
export const parseSaveFile = async (file: File): Promise<ParsedSavePreview> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<ParsedSavePreview>(
    '/api/game-files/parse-save',
    formData,
    {
      headers: {
        'Content-Type': undefined,
      },
    }
  );
  return response.data;
};

/**
 * Create a new game file from a parsed save preview.
 */
export const createGameFileFromSave = async (
  preview: ParsedSavePreview,
  gameName: string
): Promise<GameFile> => {
  const response = await api.post<GameFile>('/api/game-files/create-from-save', {
    parsed_preview: preview,
    game_name: gameName,
  });
  return response.data;
};

/**
 * Update an existing game file's pokemon roster from a parsed save preview.
 */
export const updateGameFileFromSave = async (
  gameFileId: number,
  preview: ParsedSavePreview
): Promise<GameFile> => {
  const response = await api.put<GameFile>(
    `/api/game-files/${gameFileId}/update-from-save`,
    { parsed_preview: preview }
  );
  return response.data;
};
