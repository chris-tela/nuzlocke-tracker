/**
 * Pokemon management service.
 * Handles pokemon CRUD operations, evolution, and status management.
 */
import { apiHelpers } from './api';
import type { Pokemon, BasePokemon } from '../types';
import type { StatusValue } from '../types/enums';

export interface PokemonCreate {
  poke_id: number;
  nickname?: string | null;
  nature?: string | null;
  ability?: string | null;
  level: number;
  gender?: string | null;
  status?: StatusValue | string;
}

export interface PokemonUpdate {
  level?: number;
  nickname?: string | null;
  status?: StatusValue | string | null;
  nature?: string | null;
  ability?: string | null;
}

export interface SwapResponse {
  message: string;
  partied_pokemon: Pokemon;
  swap_pokemon: Pokemon;
}

export interface StartersResponse {
  starters: BasePokemon[];
}

/**
 * Get all pokemon for a game file
 */
export const getPokemon = async (gameFileId: number): Promise<Pokemon[]> => {
  return await apiHelpers.get<Pokemon[]>(`/api/pokemon/game-files/${gameFileId}/pokemon`);
};

/**
 * Get party pokemon only
 */
export const getPartyPokemon = async (gameFileId: number): Promise<Pokemon[]> => {
  return await apiHelpers.get<Pokemon[]>(`/api/pokemon/game-files/${gameFileId}/pokemon/party`);
};

/**
 * Get stored pokemon only
 */
export const getStoredPokemon = async (gameFileId: number): Promise<Pokemon[]> => {
  return await apiHelpers.get<Pokemon[]>(`/api/pokemon/game-files/${gameFileId}/pokemon/storage`);
};

/**
 * Get fainted pokemon only
 */
export const getFaintedPokemon = async (gameFileId: number): Promise<Pokemon[]> => {
  return await apiHelpers.get<Pokemon[]>(`/api/pokemon/game-files/${gameFileId}/pokemon/fainted`);
};

/**
 * Add a pokemon to a game file
 */
export const addPokemon = async (
  gameFileId: number,
  pokemon: PokemonCreate
): Promise<Pokemon> => {
  return await apiHelpers.post<Pokemon>(
    `/api/pokemon/game-files/${gameFileId}/pokemon`,
    pokemon
  );
};

/**
 * Update a pokemon (level, nickname, status)
 */
export const updatePokemon = async (
  gameFileId: number,
  pokemonId: number,
  update: PokemonUpdate
): Promise<Pokemon> => {
  return await apiHelpers.put<Pokemon>(
    `/api/pokemon/game-files/${gameFileId}/pokemon/${pokemonId}/update`,
    update
  );
};

/**
 * Evolve a pokemon
 */
export const evolvePokemon = async (
  gameFileId: number,
  pokemonId: number,
  evolvedPokemonName: string
): Promise<Pokemon> => {
  return await apiHelpers.post<Pokemon>(
    `/api/pokemon/game-files/${gameFileId}/pokemon/${pokemonId}/evolve/${evolvedPokemonName}`
  );
};

/**
 * Swap pokemon between party and storage
 */
export const swapPokemon = async (
  gameFileId: number,
  pokemonPartyId: number,
  pokemonSwitchId: number
): Promise<SwapResponse> => {
  return await apiHelpers.post<SwapResponse>(
    `/api/pokemon/game-files/${gameFileId}/pokemon_party/${pokemonPartyId}/pokemon/${pokemonSwitchId}/swap`
  );
};

/**
 * Get base pokemon information by poke_id
 */
export const getPokemonInfo = async (pokeId: number): Promise<BasePokemon> => {
  return await apiHelpers.get<BasePokemon>(`/api/pokemon/${pokeId}`);
};

/**
 * Get base pokemon information by name
 */
export const getPokemonInfoByName = async (pokemonName: string): Promise<BasePokemon> => {
  return await apiHelpers.get<BasePokemon>(`/api/pokemon/name/${pokemonName}`);
};

/**
 * Get starter pokemon for a version
 */
export const getStarters = async (versionName: string): Promise<BasePokemon[]> => {
  const response = await apiHelpers.get<StartersResponse>(
    `/api/pokemon/versions/${versionName}/starters`
  );
  return response.starters;
};

