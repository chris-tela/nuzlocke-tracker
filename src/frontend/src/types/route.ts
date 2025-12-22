// Types related to routes and encounters, aligned with schemas & CLI usage.

// From RouteProgressResponse schema
export interface RouteProgressResponse {
  route_progress: string[];
  upcoming_routes: string[];
}

// Single encounter entry as rendered in CLI view_location:
// [pokemonName, minLevel, maxLevel, game_name, region_name, {encounter_method: chance}]
export interface RouteEncounter {
  pokemon: string;
  min_level: number;
  max_level: number;
  game_name: string;
  region: string;
  encounterMethods?: Record<string, number>; // Map of encounter method to chance percentage
}

export interface RouteDetail {
  name: string;
  version_name: string;
  encounters: RouteEncounter[];
}


