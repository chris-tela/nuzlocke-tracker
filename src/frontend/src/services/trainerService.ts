import { apiHelpers } from './api';
import type { Trainer } from '../types/trainer';

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
