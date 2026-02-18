import { apiHelpers } from './api';
import type { Trainer, TrainerMatchupResponse, TrainerMoveDetail } from '../types/trainer';

export const getTrainersByGame = async (
  gameName: string,
  starter?: string
): Promise<Trainer[]> => {
  const params = starter ? `?starter=${encodeURIComponent(starter)}` : '';
  return await apiHelpers.get<Trainer[]>(`/api/trainers/${encodeURIComponent(gameName)}${params}`);
};

export const getImportantTrainers = async (
  gameName: string,
  starter?: string
): Promise<Trainer[]> => {
  const params = starter ? `?starter=${encodeURIComponent(starter)}` : '';
  return await apiHelpers.get<Trainer[]>(
    `/api/trainers/${encodeURIComponent(gameName)}/important${params}`
  );
};

export const getTrainerMatchupSynergy = async (
  trainerId: number,
  gameFileId: number
): Promise<TrainerMatchupResponse> => {
  return await apiHelpers.get<TrainerMatchupResponse>(
    `/api/trainers/matchup/${trainerId}?gameFileId=${gameFileId}`
  );
};

export const getTrainerMoveDetails = async (
  moveNames: string[]
): Promise<TrainerMoveDetail[]> => {
  return await apiHelpers.post<TrainerMoveDetail[]>(
    '/api/trainers/moves/details',
    { names: moveNames }
  );
};
