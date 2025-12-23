/**
 * Custom hook for Pokemon data fetching with React Query
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPokemon,
  getPartyPokemon,
  getStoredPokemon,
  getFaintedPokemon,
  getPokemonInfo,
  getPokemonInfoByName,
  searchPokemon,
  addPokemon,
  updatePokemon,
  evolvePokemon,
  swapPokemon,
  getStarters,
} from '../services/pokemonService';
import { queryKeys } from './queryKeys';
import type { Pokemon, PokemonCreate, PokemonUpdate } from '../types';
import type { BasePokemon } from '../types';

export const usePokemon = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.pokemon(gameFileId) : ['pokemon', 'disabled'],
    queryFn: () => getPokemon(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const usePartyPokemon = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.partyPokemon(gameFileId) : ['pokemon', 'party', 'disabled'],
    queryFn: () => getPartyPokemon(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const useStoredPokemon = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.storedPokemon(gameFileId) : ['pokemon', 'stored', 'disabled'],
    queryFn: () => getStoredPokemon(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const useFaintedPokemon = (gameFileId: number | null) => {
  return useQuery({
    queryKey: gameFileId ? queryKeys.faintedPokemon(gameFileId) : ['pokemon', 'fainted', 'disabled'],
    queryFn: () => getFaintedPokemon(gameFileId!),
    enabled: !!gameFileId,
  });
};

export const usePokemonInfo = (pokeId: number | null) => {
  return useQuery({
    queryKey: pokeId ? queryKeys.pokemonInfo(pokeId) : ['pokemon', 'info', 'disabled'],
    queryFn: () => getPokemonInfo(pokeId!),
    enabled: !!pokeId,
  });
};

export const usePokemonInfoByName = (pokemonName: string | null) => {
  return useQuery({
    queryKey: pokemonName ? ['pokemon', 'info', 'name', pokemonName] : ['pokemon', 'info', 'name', 'disabled'],
    queryFn: () => getPokemonInfoByName(pokemonName!),
    enabled: !!pokemonName,
  });
};

export const useSearchPokemon = (query: string | null, limit: number = 10) => {
  return useQuery({
    queryKey: query ? ['pokemon', 'search', query, limit] : ['pokemon', 'search', 'disabled'],
    queryFn: () => searchPokemon(query!, limit),
    enabled: !!query && query.length >= 1,
    staleTime: 30000, // Cache for 30 seconds
  });
};

export const useVersionStarters = (versionName: string | null) => {
  return useQuery({
    queryKey: versionName ? queryKeys.versionStarters(versionName) : ['starters', 'disabled'],
    queryFn: () => getStarters(versionName!),
    enabled: !!versionName,
  });
};

export const useAddPokemon = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (pokemon: PokemonCreate) => addPokemon(gameFileId!, pokemon),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.pokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.partyPokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.storedPokemon(gameFileId) });
      }
    },
  });
};

export const useUpdatePokemon = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pokemonId, update }: { pokemonId: number; update: PokemonUpdate }) =>
      updatePokemon(gameFileId!, pokemonId, update),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.pokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.partyPokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.storedPokemon(gameFileId) });
      }
    },
  });
};

export const useEvolvePokemon = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pokemonId, evolvedPokemonName }: { pokemonId: number; evolvedPokemonName: string }) =>
      evolvePokemon(gameFileId!, pokemonId, evolvedPokemonName),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.pokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.partyPokemon(gameFileId) });
      }
    },
  });
};

export const useSwapPokemon = (gameFileId: number | null) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pokemonPartyId, pokemonSwitchId }: { pokemonPartyId: number; pokemonSwitchId: number }) =>
      swapPokemon(gameFileId!, pokemonPartyId, pokemonSwitchId),
    onSuccess: () => {
      if (gameFileId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.pokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.partyPokemon(gameFileId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.storedPokemon(gameFileId) });
      }
    },
  });
};

