/**
 * Route and encounter management service.
 * Handles route progression and encounter data.
 */
import { apiHelpers } from './api';
import type { PokemonCreate } from './pokemonService';
import type { Pokemon } from '../types';

export interface RouteListResponse {
  data: string[];
}

export interface RouteDetailResponse {
  route: string;
  data: unknown[]; // Encounter data array
}

export interface RouteProgressApiResponse {
  routes_discovered: string[];
}

export interface UpcomingRoutesResponse {
  upcoming_routes: string[];
}

export interface AddRouteResponse {
  message: string;
  route_progress: string[];
}

/**
 * Get ordered route list for a game file
 */
export const getRoutes = async (gameFileId: number): Promise<string[]> => {
  const response = await apiHelpers.get<RouteListResponse>(
    `/api/routes/game-files/${gameFileId}/routes`
  );
  return response.data;
};

/**
 * Get encounter data for a route by ID or name
 * Requires version_id to ensure version-specific encounters
 */
export const getRouteEncounters = async (
  versionId: number,
  route: string | number
): Promise<RouteDetailResponse> => {
  return await apiHelpers.get<RouteDetailResponse>(`/api/routes/${versionId}/${route}`);
};

/**
 * Get route progress for a game file
 */
export const getRouteProgress = async (gameFileId: number): Promise<string[]> => {
  const response = await apiHelpers.get<RouteProgressApiResponse>(
    `/api/routes/game-files/${gameFileId}/route-progress`
  );
  return response.routes_discovered;
};

/**
 * Get upcoming routes for a game file
 */
export const getUpcomingRoutes = async (gameFileId: number): Promise<string[]> => {
  const response = await apiHelpers.get<UpcomingRoutesResponse>(
    `/api/routes/game-files/${gameFileId}/upcoming_routes`
  );
  return response.upcoming_routes;
};

/**
 * Mark a route as progressed/completed
 */
export const addRouteProgress = async (
  gameFileId: number,
  route: string
): Promise<AddRouteResponse> => {
  return await apiHelpers.post<AddRouteResponse>(
    `/api/routes/game-files/${gameFileId}/route-progressed/${route}`
  );
};

/**
 * Add a pokemon encountered on a specific route
 */
export const addPokemonFromRoute = async (
  gameFileId: number,
  routeName: string,
  pokemon: PokemonCreate
): Promise<Pokemon> => {
  return await apiHelpers.post<Pokemon>(
    `/api/routes/game-files/${gameFileId}/route-pokemon/${routeName}`,
    pokemon
  );
};

