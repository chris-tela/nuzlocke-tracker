import type { NatureValue, StatusValue } from './enums';

// Matches PokemonResponse schema shape (snake_case fields)

export interface Pokemon {
  id: number;
  game_file_id: number;

  poke_id: number;
  name: string;
  nickname?: string | null;
  nature?: NatureValue | string | null;
  ability?: string | null;
  types: string[];
  level: number;
  gender?: string | null;
  status: StatusValue | string;
  caught_on?: string | null;
  evolution_data?: EvolutionData[] | null;
  created_at?: string | null;
}

export interface EvolutionData {
  // Very loosely typed – matches evolution_data JSON structure from backend
  evolves_to: {
    species: string;
    evolution_details?: Array<Record<string, unknown>>;
  };
}

// View model for AllPokemon when needed in UI
export interface BasePokemon {
  id: number;
  poke_id: number;
  name: string;
  types: string[];
  abilities: string[];
  weight: number;
  base_hp: number;
  base_attack: number;
  base_defense: number;
  base_special_attack: number;
  base_special_defense: number;
  base_speed: number;
  evolution_data?: EvolutionData[] | null;
  created_at: string;
}


