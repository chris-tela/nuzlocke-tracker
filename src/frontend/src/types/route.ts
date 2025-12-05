// Types related to routes and encounters, aligned with schemas & CLI usage.

// From RouteProgressResponse schema
export interface RouteProgressResponse {
  route_progress: string[];
  upcoming_routes: string[];
}

// Single encounter entry as rendered in CLI view_location:
// [pokemonName, minLevel, maxLevel, region, methods?]
export interface RouteEncounter {
  pokemon: string;
  min_level: number;
  max_level: number;
  region: string;
  methods?: string[] | string;
}

export interface RouteDetail {
  name: string;
  version_name: string;
  encounters: RouteEncounter[];
}


