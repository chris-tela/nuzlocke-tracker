import { useQuery } from '@tanstack/react-query';
import {
  getTrainersByGame,
  getImportantTrainers,
} from '../services/trainerService';
import { queryKeys } from './queryKeys';

export const useTrainersByGame = (gameName: string | null, starter?: string) => {
  return useQuery({
    queryKey: gameName
      ? queryKeys.trainers(gameName, starter)
      : ['trainers', 'disabled'],
    queryFn: () => getTrainersByGame(gameName!, starter),
    enabled: !!gameName,
  });
};

export const useImportantTrainers = (gameName: string | null, starter?: string) => {
  return useQuery({
    queryKey: gameName
      ? queryKeys.importantTrainers(gameName, starter)
      : ['trainers', 'important', 'disabled'],
    queryFn: () => getImportantTrainers(gameName!, starter),
    enabled: !!gameName,
  });
};
