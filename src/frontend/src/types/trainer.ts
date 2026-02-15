export interface TrainerPokemonStats {
  hp: number;
  attack: number;
  defense: number;
  special_attack: number;
  special_defense: number;
  speed: number;
}

export interface TrainerPokemon {
  name: string;
  poke_id: number | null;
  index?: string | null;
  level: number;
  types?: string[] | null;
  ability?: string | null;
  item?: string | null;
  nature?: string | null;
  ivs?: Record<string, number> | null;
  dvs?: Record<string, number> | null;
  evs?: Record<string, number> | null;
  moves: string[];
  stats: TrainerPokemonStats | null;
  [key: string]: unknown;
}

export interface Trainer {
  id: number;
  generation: number;
  game_names: string[];
  trainer_name: string;
  trainer_image: string;
  location: string;
  route_id: number | null;
  is_important: boolean;
  importance_reason: string | null;
  starter_filter: string | null;
  battle_order: number;
  pokemon: TrainerPokemon[];
}

export interface TrainerMatchupResponse {
  score_percent: number;
}
