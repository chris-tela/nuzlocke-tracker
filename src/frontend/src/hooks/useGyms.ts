/**
 * Custom hook for Gyms data fetching with React Query
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getGymProgress,
  getUpcomingGyms,
  addGym,
  getVersionGyms,
} from '../services/gymService';
import { queryKeys } from './queryKeys';

export const useGymProgress = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.gymProgress(gameFileId) : ['gyms', 'progress', 'disabled'],
    queryFn: () => getGymProgress(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const useUpcomingGyms = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.upcomingGyms(gameFileId) : ['gyms', 'upcoming', 'disabled'],
    queryFn: () => getUpcomingGyms(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const useVersionGyms = (versionName: string | null) => {
  return useQuery({
    queryKey: versionName ? queryKeys.versionGyms(versionName) : ['gyms', 'version', 'disabled'],
    queryFn: () => getVersionGyms(versionName!),
    enabled: !!versionName,
  });
};

export const useAddGym = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (gymNumber: number) => addGym(gameFileId!, gymNumber),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.gymProgress(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.upcomingGyms(gameFileId) });
      }
    },
  });
};

