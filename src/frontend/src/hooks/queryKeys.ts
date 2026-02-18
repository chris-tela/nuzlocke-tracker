/**
 * React Query keys for consistent cache management
 */
export const queryKeys = {
  // User queries
  user: ['user'] as const,
  
  // Game file queries
  gameFiles: ['gameFiles'] as const,
  gameFile: (id: number) => ['gameFiles', id] as const,
  
  // Pokemon queries
  pokemon: (gameFileId: number) => ['pokemon', gameFileId] as const,
  partyPokemon: (gameFileId: number) => ['pokemon', gameFileId, 'party'] as const,
  storedPokemon: (gameFileId: number) => ['pokemon', gameFileId, 'stored'] as const,
  faintedPokemon: (gameFileId: number) => ['pokemon', gameFileId, 'fainted'] as const,
  pokemonInfo: (pokeId: number) => ['pokemon', 'info', pokeId] as const,
  teamSynergy: (gameFileId: number) => ['pokemon', gameFileId, 'team-synergy'] as const,
  
  // Route queries
  routes: (gameFileId: number) => ['routes', gameFileId] as const,
  routeProgress: (gameFileId: number) => ['routes', gameFileId, 'progress'] as const,
  upcomingRoutes: (gameFileId: number) => ['routes', gameFileId, 'upcoming'] as const,
  routeEncounters: (route: string | number) => ['routes', 'encounters', route] as const,
  
  // Gym queries
  gymProgress: (gameFileId: number) => ['gyms', gameFileId, 'progress'] as const,
  upcomingGyms: (gameFileId: number) => ['gyms', gameFileId, 'upcoming'] as const,
  versionGyms: (versionName: string) => ['gyms', 'version', versionName] as const,
  
  // Trainer queries
  trainers: (gameName: string, starter?: string) =>
    ['trainers', gameName, starter ?? 'all'] as const,
  importantTrainers: (gameName: string, starter?: string) =>
    ['trainers', gameName, 'important', starter ?? 'all'] as const,

  // Version queries
  versions: ['versions'] as const,
  version: (versionName: string) => ['versions', versionName] as const,
  generations: ['generations'] as const,
  generation: (generationId: number) => ['generations', generationId] as const,
  generationStarters: (generationId: number) => ['generations', generationId, 'starters'] as const,
  versionStarters: (versionName: string) => ['versions', versionName, 'starters'] as const,
};

