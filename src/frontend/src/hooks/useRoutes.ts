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
} from '../services/routeService';
import { queryKeys } from './queryKeys';
import type { PokemonCreate } from '../services/pokemonService';

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

export const useRouteEncounters = (route: string | number | null) => {
  return useQuery({
    queryKey: route ? queryKeys.routeEncounters(route) : ['routes', 'encounters', 'disabled'],
    queryFn: () => getRouteEncounters(route!),
    enabled: !!route,
  });
};

export const useAddRouteProgress = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (route: string) => addRouteProgress(gameFileId!, route),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.routeProgress(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.upcomingRoutes(gameFileId) });
      }
    },
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
      }
    },
  });
};

