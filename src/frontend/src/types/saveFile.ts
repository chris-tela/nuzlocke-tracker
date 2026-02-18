export interface ParsedPokemonPreview {
  poke_id: number;
  name: string;
  nickname?: string | null;
  nature?: string | null;
  ability?: string | null;
  level: number;
  status: string;
  caught_on?: string | null;
}

export interface ParsedSavePreview {
  generation: number;
  game: string;
  compatible_versions: string[];
  trainer_name: string;
  badges: string[];
  pokemon: ParsedPokemonPreview[];
}
