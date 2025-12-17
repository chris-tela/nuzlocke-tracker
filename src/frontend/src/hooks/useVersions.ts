/**
 * Custom hook for Versions data fetching with React Query
 */
import { useQuery } from '@tanstack/react-query';
import { getVersions, getVersion, getGenerations, getGeneration, getGenerationStarters } from '../services/versionService';
import { queryKeys } from './queryKeys';

export const useVersions = () => {
  return useQuery({
    queryKey: queryKeys.versions,
    queryFn: () => getVersions(),
  });
};

export const useVersion = (versionName: string | null) => {
  return useQuery({
    queryKey: versionName ? queryKeys.version(versionName) : ['versions', 'disabled'],
    queryFn: () => getVersion(versionName!),
    enabled: !!versionName,
  });
};

export const useGenerations = () => {
  return useQuery({
    queryKey: queryKeys.generations,
    queryFn: () => getGenerations(),
  });
};

export const useGeneration = (generationId: number | null) => {
  return useQuery({
    queryKey: generationId ? queryKeys.generation(generationId) : ['generations', 'disabled'],
    queryFn: () => getGeneration(generationId!),
    enabled: !!generationId,
  });
};

export const useGenerationStarters = (generationId: number | null) => {
  return useQuery({
    queryKey: generationId ? queryKeys.generationStarters(generationId) : ['generations', 'starters', 'disabled'],
    queryFn: () => getGenerationStarters(generationId!),
    enabled: !!generationId,
  });
};

