import { apiHelpers } from './api';
import type { Trainer, TrainerMatchupResponse } from '../types/trainer';

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

export const getTrainersByRoute = async (
  routeId: number,
  starter?: string
): Promise<Trainer[]> => {
  const params = starter ? `?starter=${encodeURIComponent(starter)}` : '';
  return await apiHelpers.get<Trainer[]>(`/api/trainers/by-route/${routeId}${params}`);
};

export const getTrainerMatchupSynergy = async (
  trainerId: number,
  gameFileId: number
): Promise<TrainerMatchupResponse> => {
  return await apiHelpers.get<TrainerMatchupResponse>(
    `/api/trainers/matchup/${trainerId}?gameFileId=${gameFileId}`
  );
};
