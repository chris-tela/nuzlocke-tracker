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
  level: number;
  moves: string[];
  stats: TrainerPokemonStats | null;
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
