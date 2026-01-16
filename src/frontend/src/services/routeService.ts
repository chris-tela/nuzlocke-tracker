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

export interface DerivedRoutesResponse {
  derived_routes: string[];
}

export interface ParentRouteResponse {
  parent_route: string | null;
  is_derived: boolean;
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
  route: string,
  includeParent: boolean = false
): Promise<AddRouteResponse> => {
  const url = `/api/routes/game-files/${gameFileId}/route-progressed/${route}${includeParent ? '?include_parent=true' : ''}`;
  return await apiHelpers.post<AddRouteResponse>(url);
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

/**
 * Get routes that are derived from a given route name
 */
export const getDerivedRoutes = async (
  gameFileId: number,
  routeName: string
): Promise<string[]> => {
  const response = await apiHelpers.get<DerivedRoutesResponse>(
    `/api/routes/game-files/${gameFileId}/derived-routes/${routeName}`
  );
  return response.derived_routes;
};

/**
 * Get the parent route for a derived route
 */
export const getParentRoute = async (
  gameFileId: number,
  routeName: string
): Promise<ParentRouteResponse> => {
  return await apiHelpers.get<ParentRouteResponse>(
    `/api/routes/game-files/${gameFileId}/parent-route/${routeName}`
  );
};

