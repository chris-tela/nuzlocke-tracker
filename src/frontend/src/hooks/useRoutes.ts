/**
 * Custom hook for Routes data fetching with React Query
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRoutes,
  getRouteProgress,
  getUpcomingRoutes,
  getRouteEncounters,
  addRouteProgress,
  addPokemonFromRoute,
  getDerivedRoutes,
  getParentRoute,
} from '../services/routeService';
import { queryKeys } from './queryKeys';
import type { PokemonCreate } from '../services/pokemonService';
import { useVersion } from './useVersions';

export const useRoutes = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.routes(gameFileId) : ['routes', 'disabled'],
    queryFn: () => getRoutes(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const useRouteProgress = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.routeProgress(gameFileId) : ['routes', 'progress', 'disabled'],
    queryFn: () => getRouteProgress(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const useUpcomingRoutes = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.upcomingRoutes(gameFileId) : ['routes', 'upcoming', 'disabled'],
    queryFn: () => getUpcomingRoutes(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const useRouteEncounters = (route: string | number | null, gameName: string | null) => {
  const { data: version, isLoading: isLoadingVersion } = useVersion(gameName);
  
  return useQuery({
    queryKey: route && version ? queryKeys.routeEncounters(route) : ['routes', 'encounters', 'disabled'],
    queryFn: async () => {
      if (!version) {
        throw new Error('Version not found');
      }
      try {
        return await getRouteEncounters(version.version_id, route!);
      } catch (error: any) {
        // Handle 404s gracefully - some routes (gyms, special locations) don't have encounter data
        if (error?.response?.status === 404) {
          return { route: route as string, data: [], route_id: null as number | null };
        }
        throw error;
      }
    },
    enabled: !!route && !!version && !isLoadingVersion,
    retry: false, // Don't retry 404s
  });
};

export const useAddRouteProgress = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ route, includeParent }: { route: string; includeParent?: boolean }) => 
      addRouteProgress(gameFileId!, route, includeParent || false),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.routeProgress(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.upcomingRoutes(gameFileId) });
      }
    },
  });
};

export const useParentRoute = (gameFileId: number | null, routeName: string | null) => {
  return useQuery({
    queryKey: gameFileId && routeName ? ['parentRoute', gameFileId, routeName] : ['parentRoute', 'disabled'],
    queryFn: () => getParentRoute(gameFileId!, routeName!),
    enabled: !!gameFileId && !!routeName,
  });
};

export const useAddPokemonFromRoute = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ routeName, pokemon }: { routeName: string; pokemon: PokemonCreate }) =>
      addPokemonFromRoute(gameFileId!, routeName, pokemon),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.pokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.partyPokemon(gameFileId) });
        // Also invalidate route queries so the route moves to encountered
        queryClient.invalidateQueries({ queryKey: queryKeys.routeProgress(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.upcomingRoutes(gameFileId) });
      }
    },
  });
};

export const useDerivedRoutes = (gameFileId: number | null, routeName: string | null) => {
  return useQuery({
    queryKey: gameFileId && routeName ? ['derivedRoutes', gameFileId, routeName] : ['derivedRoutes', 'disabled'],
    queryFn: () => getDerivedRoutes(gameFileId!, routeName!),
    enabled: !!gameFileId && !!routeName,
  });
};

